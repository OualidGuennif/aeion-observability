"""Supervisor-owned SQLite state for the factory queue, claims, events and cancellation.

Every transition verifies its precondition, records an event and persists atomically.
State lives under the ignored ``demo/.local/factory/`` tree, never inside the product.
"""
import hashlib
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from .manifest import ManifestError

PROPOSED = "proposed"
QUEUED = "queued"
DISPATCHED = "dispatched"
BUILT = "built"
GATED = "gated"
PR_OPEN = "pr_open"
APPROVED = "approved"
MERGED = "merged"
HELD = "held"
FAILED = "failed"
CANCELLED = "cancelled"
SIMULATED_COMPLETE = "simulated_complete"

NONTERMINAL = {PROPOSED, QUEUED, DISPATCHED, BUILT, GATED, PR_OPEN, APPROVED, HELD}
TERMINAL = {MERGED, FAILED, CANCELLED, SIMULATED_COMPLETE}
ACTIVE = {DISPATCHED}
HOLD_REASONS = {
    "dependency_missing", "profile_expired", "sandbox_unqualified", "budget_unavailable",
    "qualification_missing", "owner_review_required", "reconciliation_needed",
    # No usable gateway session: an agent that cannot authenticate does not start building.
    "credential_unavailable",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS builds (
  build_id TEXT PRIMARY KEY,
  feature_id TEXT NOT NULL,
  status TEXT NOT NULL,
  hold_reason TEXT,
  idempotency_key TEXT NOT NULL,
  payload_digest TEXT NOT NULL,
  catalog_digest TEXT NOT NULL,
  attempt_id TEXT,
  attempt_generation INTEGER,
  cancellation_generation INTEGER NOT NULL DEFAULT 0,
  lease_until_ns INTEGER,
  receipt TEXT,
  created_ns INTEGER NOT NULL,
  updated_ns INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_idem ON builds(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_status ON builds(status);

CREATE TABLE IF NOT EXISTS events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  build_id TEXT NOT NULL,
  time_ns INTEGER NOT NULL,
  actor TEXT NOT NULL,
  event TEXT NOT NULL,
  detail TEXT,
  generation INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_build ON events(build_id, seq);

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""

DEFAULT_LEASE_NS = 60 * 1_000_000_000


class StoreError(ValueError):
    """A factory store precondition violation."""


class Store:
    def __init__(self, path, active_concurrency=1, simulated_dependencies=False):
        self.path = str(path)
        self.active_concurrency = int(active_concurrency)
        # Only the local playground sets this: there a simulated build satisfies a dependency,
        # never in a deployment where a merge is the only evidence.
        self.simulated_dependencies = bool(simulated_dependencies)
        self._lock = threading.RLock()
        Path(self.path).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._init_schema()
        self.reconcile()

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(SCHEMA)
                conn.commit()
            finally:
                conn.close()

    @staticmethod
    def _now():
        return time.time_ns()

    @staticmethod
    def _event(conn, build_id, now, actor, event, detail, generation):
        conn.execute(
            "INSERT INTO events (build_id, time_ns, actor, event, detail, generation) VALUES (?,?,?,?,?,?)",
            (build_id, now, actor, event, detail, generation),
        )

    @staticmethod
    def _row(conn, build_id):
        row = conn.execute("SELECT * FROM builds WHERE build_id=?", (build_id,)).fetchone()
        return dict(row) if row is not None else None

    @staticmethod
    def _rows(conn, clause="", args=()):
        rows = conn.execute(f"SELECT * FROM builds {clause} ORDER BY created_ns", args).fetchall()
        return [dict(r) for r in rows]

    def _merged_ids(self, conn):
        """Dependencies count as satisfied by a merge — or by a simulated build, in the playground."""
        if getattr(self, "simulated_dependencies", False):
            rows = conn.execute("SELECT feature_id FROM builds WHERE status IN (?,?)",
                                (MERGED, SIMULATED_COMPLETE))
        else:
            rows = conn.execute("SELECT feature_id FROM builds WHERE status=?", (MERGED,))
        return {r["feature_id"] for r in rows}

    # ------------------------------------------------------------------ admission
    def admit(self, feature_ids, idempotency_key, catalog, actor="owner"):
        """Admit one or more feature ids. Missing dependencies hold; replay returns the same builds."""
        if not feature_ids or not idempotency_key:
            raise StoreError("missing_ids_or_key")
        ids = []
        for fid in feature_ids:
            if fid not in catalog.by_id:
                raise StoreError(f"unknown_feature:{fid}")
            if fid in ids:
                raise StoreError(f"duplicate_feature:{fid}")
            ids.append(fid)
        if len(ids) > 10:
            raise StoreError("too_many_ids")
        payload_digest = hashlib.sha256(
            json.dumps({"ids": sorted(ids), "catalog": catalog.digest}, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    existing = conn.execute(
                        "SELECT payload_digest FROM builds WHERE idempotency_key=?", (idempotency_key,)
                    ).fetchone()
                    if existing is not None:
                        if existing["payload_digest"] != payload_digest:
                            return {"status": "conflict", "build_ids": []}
                        return {"status": "replayed", "build_ids": [b["build_id"] for b in self._rows(conn, "WHERE idempotency_key=?", (idempotency_key,))]}
                    nonterminal = conn.execute(
                        f"SELECT COUNT(*) AS c FROM builds WHERE status IN ({','.join('?' * len(NONTERMINAL))})",
                        tuple(NONTERMINAL),
                    ).fetchone()["c"]
                    if nonterminal + len(ids) > 10:
                        return {"status": "cap_exceeded", "build_ids": []}
                    merged = self._merged_ids(conn)
                    now = self._now()
                    created = []
                    for fid in ids:
                        build_id = uuid.uuid4().hex
                        missing = catalog.missing_dependencies(fid, merged)
                        status = HELD if missing else QUEUED
                        reason = "dependency_missing" if missing else None
                        conn.execute(
                            "INSERT INTO builds (build_id, feature_id, status, hold_reason, idempotency_key, "
                            "payload_digest, catalog_digest, created_ns, updated_ns) VALUES (?,?,?,?,?,?,?,?,?)",
                            (build_id, fid, status, reason, idempotency_key, payload_digest, catalog.digest, now, now),
                        )
                        self._event(conn, build_id, now, actor, PROPOSED, None, 0)
                        self._event(conn, build_id, now, actor, status,
                                    json.dumps({"missing": missing}) if missing else None, 0)
                        created.append(build_id)
                    return {"status": "admitted", "build_ids": created}
            finally:
                conn.close()

    # ------------------------------------------------------------------ dispatch
    def claim_next(self, catalog, lease_ns=DEFAULT_LEASE_NS):
        """Claim the next queued build, honouring the active-concurrency and disjointness rules."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    active = self._rows(conn, "WHERE status=?", (DISPATCHED,))
                    if len(active) >= self.active_concurrency:
                        return None
                    candidate = conn.execute("SELECT * FROM builds WHERE status=? ORDER BY created_ns LIMIT 1", (QUEUED,)).fetchone()
                    if candidate is None:
                        return None
                    if active and any(not self._disjoint(catalog, a["feature_id"], candidate["feature_id"]) for a in active):
                        return None
                    now = self._now()
                    attempt_id = uuid.uuid4().hex
                    generation = candidate["cancellation_generation"]
                    conn.execute(
                        "UPDATE builds SET status=?, attempt_id=?, attempt_generation=?, lease_until_ns=?, updated_ns=? WHERE build_id=?",
                        (DISPATCHED, attempt_id, generation, now + lease_ns, now, candidate["build_id"]),
                    )
                    self._event(conn, candidate["build_id"], now, "supervisor", DISPATCHED,
                                json.dumps({"attempt_id": attempt_id}), generation)
                    return self._row(conn, candidate["build_id"])
            finally:
                conn.close()

    @staticmethod
    def _disjoint(catalog, fa, fb):
        """Two candidates may run together only if both are parallel, unrelated and write disjoint scopes."""
        a, b = catalog.by_id[fa], catalog.by_id[fb]
        if not (a["parallel"] and b["parallel"]):
            return False
        if Store._reachable(catalog, fa, fb) or Store._reachable(catalog, fb, fa):
            return False
        return not any(_scopes_overlap(pa, pb) for pa in a["write_paths"] for pb in b["write_paths"])

    @staticmethod
    def _reachable(catalog, start, target):
        seen = set()
        stack = [start]
        while stack:
            node = stack.pop()
            for dep in catalog.by_id[node]["depends_on"]:
                if dep == target:
                    return True
                if dep not in seen:
                    seen.add(dep)
                    stack.append(dep)
        return False

    # ------------------------------------------------------------------ completion
    def complete_attempt(self, attempt_id, generation, receipt, terminal=SIMULATED_COMPLETE):
        """Finish a claimed attempt. A cancelled/stale generation cannot advance."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    row = conn.execute("SELECT * FROM builds WHERE attempt_id=?", (attempt_id,)).fetchone()
                    if row is None:
                        return {"status": "unknown_attempt"}
                    if row["attempt_generation"] != generation or row["cancellation_generation"] != generation:
                        return {"status": "stale_attempt"}
                    if row["status"] != DISPATCHED:
                        return {"status": "not_dispatched"}
                    if terminal not in TERMINAL:
                        raise StoreError(f"invalid_terminal:{terminal}")
                    now = self._now()
                    conn.execute(
                        "UPDATE builds SET status=?, receipt=?, lease_until_ns=NULL, updated_ns=? WHERE build_id=?",
                        (terminal, json.dumps(receipt), now, row["build_id"]),
                    )
                    self._event(conn, row["build_id"], now, "worker", BUILT, None, generation)
                    self._event(conn, row["build_id"], now, "worker", terminal, json.dumps(receipt), generation)
                    return {"status": "completed", "build_id": row["build_id"]}
            finally:
                conn.close()

    # ------------------------------------------------------------------ cancellation
    def hold_dispatched(self, build_id, reason, actor="supervisor"):
        """Hold a dispatched build before its worker launches (e.g. a failed freeze)."""
        if reason not in HOLD_REASONS:
            raise StoreError(f"invalid_hold_reason:{reason}")
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    row = conn.execute("SELECT * FROM builds WHERE build_id=?", (build_id,)).fetchone()
                    if row is None:
                        return {"status": "not_found"}
                    if row["status"] != DISPATCHED:
                        return {"status": "not_dispatched"}
                    now = self._now()
                    conn.execute(
                        "UPDATE builds SET status=?, hold_reason=?, attempt_id=NULL, attempt_generation=NULL, lease_until_ns=NULL, updated_ns=? WHERE build_id=?",
                        (HELD, reason, now, build_id),
                    )
                    self._event(conn, build_id, now, actor, HELD, json.dumps({"reason": reason}), row["cancellation_generation"])
                    return {"status": "held", "reason": reason}
            finally:
                conn.close()

    def cancel(self, build_id, actor="owner"):
        """Cancel a nonterminal build and bump its cancellation generation."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    row = conn.execute("SELECT * FROM builds WHERE build_id=?", (build_id,)).fetchone()
                    if row is None:
                        return {"status": "not_found"}
                    if row["status"] in TERMINAL:
                        return {"status": "already_terminal"}
                    generation = row["cancellation_generation"] + 1
                    now = self._now()
                    conn.execute(
                        "UPDATE builds SET status=?, cancellation_generation=?, lease_until_ns=NULL, updated_ns=? WHERE build_id=?",
                        (CANCELLED, generation, now, build_id),
                    )
                    self._event(conn, build_id, now, actor, CANCELLED, None, generation)
                    return {"status": "cancelled", "generation": generation}
            finally:
                conn.close()

    # ------------------------------------------------------------------ recovery
    def reconcile(self):
        """Reset expired dispatched leases back to queued; never blindly redispatch."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    now = self._now()
                    rows = conn.execute("SELECT * FROM builds WHERE status=? AND lease_until_ns < ?", (DISPATCHED, now)).fetchall()
                    for row in rows:
                        conn.execute(
                            "UPDATE builds SET status=?, attempt_id=NULL, attempt_generation=NULL, lease_until_ns=NULL, updated_ns=? WHERE build_id=?",
                            (QUEUED, now, row["build_id"]),
                        )
                        self._event(conn, row["build_id"], now, "supervisor", "reconciled",
                                    json.dumps({"attempt_id": row["attempt_id"]}), row["cancellation_generation"])
                    return len(rows)
            finally:
                conn.close()

    # ------------------------------------------------------------------ reads / fixtures
    def meta_get(self, key, default=None):
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
                return row["value"] if row is not None else default
            finally:
                conn.close()

    def meta_set(self, key, value):
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        "INSERT INTO meta (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, value),
                    )
            finally:
                conn.close()

    def by_attempt(self, attempt_id):
        """Look a build up by the attempt the worker recorded; used by the publisher process."""
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute("SELECT * FROM builds WHERE attempt_id=?", (attempt_id,)).fetchone()
                return dict(row) if row is not None else None
            finally:
                conn.close()

    def board(self):
        with self._lock:
            conn = self._connect()
            try:
                return self._rows(conn)
            finally:
                conn.close()

    def events(self, build_id, after_seq=0):
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT * FROM events WHERE build_id=? AND seq>? ORDER BY seq", (build_id, after_seq)
                ).fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def nonterminal_count(self):
        with self._lock:
            conn = self._connect()
            try:
                return conn.execute(
                    f"SELECT COUNT(*) AS c FROM builds WHERE status IN ({','.join('?' * len(NONTERMINAL))})",
                    tuple(NONTERMINAL),
                ).fetchone()["c"]
            finally:
                conn.close()

    def seed_merged(self, feature_id, catalog, actor="fixture"):
        """Label a fixture dependency as already merged in the admitted base (tests/fixtures only)."""
        if feature_id not in catalog.by_id:
            raise StoreError(f"unknown_feature:{feature_id}")
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    build_id = uuid.uuid4().hex
                    now = self._now()
                    conn.execute(
                        "INSERT INTO builds (build_id, feature_id, status, idempotency_key, payload_digest, "
                        "catalog_digest, receipt, created_ns, updated_ns) VALUES (?,?,?,?,?,?,?,?,?)",
                        (build_id, feature_id, MERGED, f"fixture-merged-{feature_id}", "fixture", catalog.digest,
                         json.dumps({"fixture": True, "merged_base": True}), now, now),
                    )
                    self._event(conn, build_id, now, actor, MERGED, json.dumps({"fixture": True}), 0)
                    return build_id
            finally:
                conn.close()


def _scopes_overlap(a, b):
    """Literal file or directory-prefix scopes overlap when one contains the other."""
    if a == b:
        return True
    if a.endswith("/") and b.startswith(a):
        return True
    if b.endswith("/") and a.startswith(b):
        return True
    return False
