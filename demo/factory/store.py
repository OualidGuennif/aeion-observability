"""Supervisor-owned SQLite state for the factory queue, claims, events and cancellation.

Every transition verifies its precondition, records an event and persists atomically.
State lives under the ignored ``demo/.local/factory/`` tree, never inside the product.
"""
import hashlib
import json
import re
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
LIVE_COMPLETE = "live_complete"
BASELINE = "baseline"

NONTERMINAL = {PROPOSED, QUEUED, DISPATCHED, BUILT, GATED, PR_OPEN, APPROVED, HELD}
TERMINAL = {MERGED, FAILED, CANCELLED, SIMULATED_COMPLETE, LIVE_COMPLETE, BASELINE}
COMPLETED_FEATURE = {MERGED, BASELINE, LIVE_COMPLETE}
IN_PROGRESS_FEATURE = {QUEUED, DISPATCHED, BUILT, GATED, PR_OPEN, APPROVED, HELD}
ACTIVE = {DISPATCHED, GATED, PR_OPEN, APPROVED}
PROGRESS_PHASES = {'preparing', 'building', 'checking', 'reviewing', 'publishing',
    'waiting_ci', 'merging', 'model.step.started', 'tool.finished', 'gen_ai.request',
    'gate.closed', 'process.started', 'process.retired', 'protected_check.started',
    'protected_check.finished', 'handover.prepared'}
HOLD_REASONS = {
    "dependency_missing", "profile_expired", "sandbox_unqualified", "budget_unavailable",
    "qualification_missing", "owner_review_required", "reconciliation_needed",
    # The pinned base cannot be cloned, checked out or matched exactly.
    "base_unavailable",
    # No usable gateway session: an agent that cannot authenticate does not start building.
    "credential_unavailable",
    # The configured execution (target, builder or mode) is unavailable or unknown.
    "execution_unavailable", "execution_mode_unknown",
    # A pinned target profile belongs to one feature and cannot freeze another.
    "target_feature_mismatch",
    "target_unavailable", "worker_error",
    # Live was requested without a qualified builder; the request is held, never simulated.
    "live_builder_unqualified",
    # Live is configured but the provider credential is absent; no attempt is started.
    "provider_unconfigured",
    # demo/budget.conf is unreadable, unknown, above its owner ceiling or inconsistent.
    "budget_config_invalid",
    "flue_factory_unqualified", "publication_blocked", "catalog_changed", "preparation_unavailable",
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
  contract_digest TEXT NOT NULL DEFAULT '',
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
CREATE TABLE IF NOT EXISTS routing_outcomes (
  identity TEXT PRIMARY KEY,
  cohort TEXT NOT NULL,
  created_ns INTEGER NOT NULL,
  detail TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_routing_cohort ON routing_outcomes(cohort, created_ns);
CREATE TABLE IF NOT EXISTS publication_jobs (
  attempt_id TEXT PRIMARY KEY,
  generation INTEGER NOT NULL,
  request TEXT NOT NULL,
  phase TEXT NOT NULL,
  remote TEXT NOT NULL DEFAULT '{}',
  not_before_ns INTEGER NOT NULL DEFAULT 0,
  lease_owner TEXT,
  lease_until_ns INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS feature_integrations (
  feature_id TEXT NOT NULL,
  contract_digest TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  merge_sha TEXT NOT NULL,
  main_sha TEXT NOT NULL,
  observed_ns INTEGER NOT NULL,
  PRIMARY KEY(feature_id, contract_digest)
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
                conn.execute('BEGIN IMMEDIATE')
                if 'contract_digest' not in {r['name'] for r in conn.execute('PRAGMA table_info(builds)')}:
                    conn.execute("ALTER TABLE builds ADD COLUMN contract_digest TEXT NOT NULL DEFAULT ''")
                if 'contract_digest' not in {r['name'] for r in conn.execute('PRAGMA table_info(feature_integrations)')}:
                    conn.execute('ALTER TABLE feature_integrations RENAME TO legacy_feature_integrations')
                    conn.execute('CREATE TABLE feature_integrations (feature_id TEXT NOT NULL, '
                        'contract_digest TEXT NOT NULL, attempt_id TEXT NOT NULL, merge_sha TEXT NOT NULL, '
                        'main_sha TEXT NOT NULL, observed_ns INTEGER NOT NULL, PRIMARY KEY(feature_id,contract_digest))')
                    conn.execute("INSERT INTO feature_integrations SELECT feature_id,'',attempt_id,merge_sha,main_sha,observed_ns "
                                 'FROM legacy_feature_integrations')
                    conn.execute('DROP TABLE legacy_feature_integrations')
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

    def _merged_ids(self, conn, catalog):
        """Dependencies count as satisfied by a merge or a verified pinned-base baseline."""
        if getattr(self, "simulated_dependencies", False):
            rows = conn.execute("SELECT * FROM builds WHERE status IN (?,?,?)",
                                (MERGED, BASELINE, SIMULATED_COMPLETE))
        else:
            rows = conn.execute("SELECT * FROM builds WHERE status IN (?,?)",
                                (MERGED, BASELINE))
        return {r['feature_id'] for r in rows if catalog.matches_contract(dict(r))} | self._integration_ids(conn, catalog)

    @staticmethod
    def _integration_ids(conn, catalog):
        return {r['feature_id'] for r in conn.execute('SELECT * FROM feature_integrations')
                if catalog.matches_contract(dict(r))}

    @staticmethod
    def _obsolete_unstarted(row, catalog):
        return (not row['attempt_id'] and row['status'] in {QUEUED, HELD}
                and not catalog.matches_contract(row))

    @staticmethod
    def _publication_holds(conn):
        # Cancel does not prove that an in-flight remote write had no effect.
        return {r['feature_id'] for r in conn.execute(
            "SELECT b.feature_id FROM builds b JOIN publication_jobs p ON p.attempt_id=b.attempt_id "
            "WHERE b.status=? AND p.phase NOT IN ('complete','absent')", (CANCELLED,))}

    # ------------------------------------------------------------------ admission
    def feature_availability(self, catalog, target_feature=None, execution_hold=None,
                             target_required=False, target_features=None):
        """Operator states derived from persisted evidence, never browser claims."""
        rows = self.board()
        implemented = {r['feature_id'] for r in rows if r['status'] in {MERGED, BASELINE}
                       and catalog.matches_contract(r)}
        conn = self._connect()
        try:
            implemented |= self._integration_ids(conn, catalog)
            uncertain = self._publication_holds(conn)
        finally:
            conn.close()
        built = {r['feature_id'] for r in rows if r['status'] == LIVE_COMPLETE and catalog.matches_contract(r)}
        current = [r for r in rows if not self._obsolete_unstarted(r, catalog)]
        active = {r['feature_id'] for r in current if r['status'] in IN_PROGRESS_FEATURE}
        holds = {r['feature_id']: r['hold_reason'] for r in current if r['status'] == HELD}
        result = {}
        for feature in catalog.features:
            fid = feature['id']
            missing = catalog.missing_dependencies(fid, implemented)
            if fid in implemented:
                state, reason = 'implemented', 'already_implemented'
            elif fid in uncertain:
                state, reason = 'blocked', 'reconciliation_needed'
            elif fid in built:
                state, reason = 'built', 'awaiting_integration'
            elif fid in holds:
                state, reason = 'blocked', holds[fid]
            elif fid in active:
                state, reason = 'in_progress', 'feature_in_progress'
            elif not catalog.contract_current(fid):
                state, reason = 'blocked', 'catalog_changed'
            elif execution_hold:
                state, reason = 'blocked', execution_hold
            elif target_required and fid not in (target_features if target_features is not None
                                                 else [target_feature]):
                state, reason = 'blocked', 'target_unavailable'
            elif missing:
                state, reason = 'blocked', 'dependency_missing'
            else:
                state, reason = 'ready', None
            result[fid] = {'state': state, 'selectable': state == 'ready',
                           'reason': reason, 'missing_dependencies': missing}
        return result

    def admit(self, feature_ids, idempotency_key, catalog, actor="owner"):
        """Admit one or more feature ids. Missing dependencies hold; replay returns the same builds."""
        if (not isinstance(feature_ids, list) or not feature_ids
                or any(not isinstance(fid, str) for fid in feature_ids)
                or not isinstance(idempotency_key, str) or not idempotency_key):
            raise StoreError("missing_ids_or_key")
        ids = []
        for fid in feature_ids:
            if fid not in catalog.by_id:
                raise StoreError(f"unknown_feature:{fid}")
            if fid in ids:
                raise StoreError(f"duplicate_feature:{fid}")
            ids.append(fid)
            if not catalog.contract_current(fid):
                raise StoreError('catalog_changed')
        if len(ids) > 10:
            raise StoreError("too_many_ids")
        payload_digest = hashlib.sha256(
            json.dumps({"ids": sorted(ids), "contracts": {fid:catalog.contracts[fid] for fid in sorted(ids)}},
                       sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    # Serialize the read/insert across Store instances as well as HTTP threads.
                    conn.execute("BEGIN IMMEDIATE")
                    existing = conn.execute(
                        "SELECT payload_digest FROM builds WHERE idempotency_key=?", (idempotency_key,)
                    ).fetchone()
                    if existing is not None:
                        if existing["payload_digest"] != payload_digest:
                            return {"status": "conflict", "build_ids": []}
                        return {"status": "replayed", "build_ids": [b["build_id"] for b in self._rows(conn, "WHERE idempotency_key=?", (idempotency_key,))]}
                    integrated = self._integration_ids(conn, catalog)
                    uncertain = self._publication_holds(conn)
                    for fid in ids:
                        prior = self._rows(conn, 'WHERE feature_id=?', (fid,))
                        if any(r['status'] in COMPLETED_FEATURE and catalog.matches_contract(r) for r in prior) or fid in integrated:
                            raise StoreError(f"feature_already_completed:{fid}")
                        if fid in uncertain:
                            raise StoreError(f"publication_reconciliation_required:{fid}")
                        if any(r['status'] in IN_PROGRESS_FEATURE and not self._obsolete_unstarted(r,catalog) for r in prior):
                            raise StoreError(f"feature_in_progress:{fid}")
                        for row in prior:
                            if self._obsolete_unstarted(row,catalog):
                                now=self._now()
                                conn.execute('UPDATE builds SET status=?,cancellation_generation=cancellation_generation+1,updated_ns=? '
                                             'WHERE build_id=?', (CANCELLED,now,row['build_id']))
                                self._event(conn,row['build_id'],now,actor,'superseded_contract',None,
                                            row['cancellation_generation']+1)
                    nonterminal = conn.execute(
                        f"SELECT COUNT(*) AS c FROM builds WHERE status IN ({','.join('?' * len(NONTERMINAL))})",
                        tuple(NONTERMINAL),
                    ).fetchone()["c"]
                    if nonterminal + len(ids) > 10:
                        return {"status": "cap_exceeded", "build_ids": []}
                    merged = self._merged_ids(conn, catalog)
                    now = self._now()
                    created = []
                    for fid in ids:
                        build_id = uuid.uuid4().hex
                        missing = catalog.missing_dependencies(fid, merged)
                        status = HELD if missing else QUEUED
                        reason = "dependency_missing" if missing else None
                        conn.execute(
                            "INSERT INTO builds (build_id, feature_id, status, hold_reason, idempotency_key, "
                            "payload_digest, catalog_digest, contract_digest, created_ns, updated_ns) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (build_id, fid, status, reason, idempotency_key, payload_digest, catalog.digest,
                             catalog.contracts[fid], now, now),
                        )
                        self._event(conn, build_id, now, actor, PROPOSED, None, 0)
                        self._event(conn, build_id, now, actor, status,
                                    json.dumps({"missing": missing}) if missing else None, 0)
                        created.append(build_id)
                    return {"status": "admitted", "build_ids": created}
            finally:
                conn.close()

    # ------------------------------------------------------------------ dispatch
    @staticmethod
    def _baseline_digest(evidence):
        # Re-verification timing is not the identity of an immutable implementation proof.
        identity = {key: value for key, value in evidence.items() if key != 'verified_at_ns'}
        if isinstance(identity.get('check'), dict):
            identity['check'] = {key: value for key, value in identity['check'].items()
                                 if key != 'duration_ms'}
        return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def record_baseline(self, feature_id, evidence, catalog, actor="baseline"):
        """Record a verified pinned-base baseline; only the verifier calls this."""
        if feature_id not in catalog.by_id:
            raise StoreError(f"unknown_feature:{feature_id}")
        if not isinstance(evidence, dict) or not evidence.get("base_sha"):
            raise StoreError("baseline_evidence")
        if catalog.spec_dir is not None and (not catalog.contract_current(feature_id)
                or evidence.get('contract_digest') != catalog.contracts[feature_id]):
            raise StoreError('baseline_contract_unqualified')
        key = f"baseline:{feature_id}:{catalog.contracts[feature_id]}:{evidence['base_sha']}"
        payload_digest = self._baseline_digest(evidence)
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    existing = conn.execute(
                        "SELECT build_id, payload_digest FROM builds WHERE idempotency_key=?",
                        (key,)).fetchone()
                    if existing is not None:
                        if existing["payload_digest"] != payload_digest:
                            # Baselines written by the old version hashed the timestamp too.
                            prior = conn.execute('SELECT detail FROM events WHERE build_id=? AND event=? '
                                                 'ORDER BY seq LIMIT 1', (existing['build_id'], BASELINE)).fetchone()
                            if prior is None or self._baseline_digest(json.loads(prior['detail'])) != payload_digest:
                                return {"status": "conflict", "build_ids": []}
                        return {"status": "replayed", "build_ids": [existing["build_id"]]}
                    statuses = {row['status'] for row in conn.execute(
                        'SELECT status FROM builds WHERE feature_id=?', (feature_id,))}
                    if statuses & IN_PROGRESS_FEATURE:
                        raise StoreError(f'feature_in_progress:{feature_id}')
                    build_id = uuid.uuid4().hex
                    now = self._now()
                    receipt = {**evidence, 'build_id': build_id, 'feature_id': feature_id,
                               'simulated': False}
                    conn.execute(
                        "INSERT INTO builds (build_id, feature_id, status, hold_reason, idempotency_key, "
                        "payload_digest, catalog_digest, contract_digest, receipt, created_ns, updated_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (build_id, feature_id, BASELINE, None, key, payload_digest,
                         catalog.digest, catalog.contracts[feature_id], json.dumps(receipt), now, now),
                    )
                    self._event(conn, build_id, now, actor, PROPOSED, None, 0)
                    self._event(conn, build_id, now, actor, BASELINE, json.dumps(evidence), 0)
                    return {"status": "recorded", "build_ids": [build_id]}
            finally:
                conn.close()

    def record_baseline_trace(self, build_id, evidence):
        """Attach trusted exporter metadata after verification; never change the baseline proof."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row = self._row(conn, build_id)
                    if row is None or row['status'] != BASELINE:
                        raise StoreError('baseline_required')
                    receipt = json.loads(row['receipt']) if row['receipt'] else {
                        'build_id': build_id, 'feature_id': row['feature_id'], 'simulated': False}
                    receipt['telemetry'] = evidence
                    conn.execute('UPDATE builds SET receipt=? WHERE build_id=?', (json.dumps(receipt), build_id))
                    self._event(conn, build_id, self._now(), 'baseline', 'baseline_trace',
                                json.dumps(evidence), row['cancellation_generation'])
            finally:
                conn.close()

    def claim_next(self, catalog, lease_ns=DEFAULT_LEASE_NS):
        """Claim the next queued build, honouring the active-concurrency and disjointness rules."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    waiting = conn.execute('SELECT * FROM builds WHERE status=? OR '
                        '(status=? AND hold_reason=? AND attempt_id IS NULL)',
                        (QUEUED, HELD, 'dependency_missing')).fetchall()
                    merged = self._merged_ids(conn, catalog)
                    for row in waiting:
                        if not catalog.matches_contract(dict(row)):
                            status, reason = HELD, 'catalog_changed'
                        elif catalog.missing_dependencies(row['feature_id'], merged):
                            status, reason = HELD, 'dependency_missing'
                        else:
                            status, reason = QUEUED, None
                        if row['status'] != status or row['hold_reason'] != reason:
                            now = self._now()
                            conn.execute('UPDATE builds SET status=?,hold_reason=?,updated_ns=? WHERE build_id=?',
                                (status,reason,now,row['build_id']))
                            self._event(conn,row['build_id'],now,'supervisor',status,reason,row['cancellation_generation'])
                    active = self._rows(conn, f"WHERE status IN ({','.join('?' for _ in ACTIVE)})", tuple(ACTIVE))
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
    def stage_publication(self, build, request, receipt):
        """Commit the frozen outbox and nonterminal build state in one transaction."""
        body = json.dumps(request, sort_keys=True, separators=(',', ':'), allow_nan=False)
        if len(body.encode()) > 1048576:
            raise StoreError('publication_request_too_large')
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row = conn.execute('SELECT * FROM builds WHERE attempt_id=?', (build['attempt_id'],)).fetchone()
                    generation = build['attempt_generation']
                    if (row is None or row['status'] != DISPATCHED or row['attempt_generation'] != generation
                            or row['cancellation_generation'] != generation
                            or row['lease_until_ns'] is None or row['lease_until_ns']<=self._now()):
                        return False
                    if (request.get('build_id') != row['build_id'] or request.get('attempt_id') != row['attempt_id']
                            or request.get('attempt_generation') != generation):
                        raise StoreError('publication_identity_mismatch')
                    conn.execute('INSERT INTO publication_jobs(attempt_id,generation,request,phase) VALUES(?,?,?,?)',
                                 (row['attempt_id'], generation, body, 'publish'))
                    now = self._now()
                    conn.execute('UPDATE builds SET status=?,receipt=?,lease_until_ns=NULL,updated_ns=? WHERE build_id=?',
                                 (GATED, json.dumps(receipt), now, row['build_id']))
                    self._event(conn,row['build_id'],now,'supervisor',GATED,'publication_queued',generation)
                    return True
            finally:
                conn.close()

    def claim_publication(self, lease_ns=240_000_000_000):
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    now = self._now()
                    row = conn.execute("SELECT p.*,b.build_id,b.status,b.cancellation_generation FROM publication_jobs p "
                        "JOIN builds b ON b.attempt_id=p.attempt_id WHERE p.phase IN ('publish','ci') "
                        "AND b.status IN (?,?,?) AND b.cancellation_generation=p.generation "
                        'AND p.not_before_ns<=? AND p.lease_until_ns<=? ORDER BY b.created_ns LIMIT 1',
                        (GATED,PR_OPEN,APPROVED,now,now)).fetchone()
                    if row is None:
                        return None
                    owner = uuid.uuid4().hex
                    conn.execute('UPDATE publication_jobs SET lease_owner=?,lease_until_ns=? WHERE attempt_id=?',
                                 (owner,now+lease_ns,row['attempt_id']))
                    result = dict(row)
                    result.update(lease_owner=owner, request=json.loads(row['request']), remote=json.loads(row['remote']))
                    return result
            finally:
                conn.close()

    def finish_publication(self, job, result, simulated=False, delay_ns=15_000_000_000):
        """A remote response never overrides cancellation or a newer lease owner."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row = conn.execute('SELECT * FROM builds WHERE attempt_id=?', (job['attempt_id'],)).fetchone()
                    pending = conn.execute('SELECT * FROM publication_jobs WHERE attempt_id=?', (job['attempt_id'],)).fetchone()
                    if row is None or pending is None or pending['lease_owner'] != job['lease_owner']:
                        return {'status':'stale_publication'}
                    confirmed = (not simulated and result.get('status') == 'merged'
                        and result.get('confirmed_main') is True
                        and all(isinstance(result.get(k), str) and re.fullmatch('[a-f0-9]{40}',result[k])
                                for k in ('merge_sha','main_sha')))
                    if confirmed:
                        conn.execute('INSERT OR IGNORE INTO feature_integrations VALUES(?,?,?,?,?,?)',
                            (row['feature_id'],row['contract_digest'],row['attempt_id'],result['merge_sha'],result['main_sha'],self._now()))
                    if row['cancellation_generation'] != job['generation'] or row['status'] not in {GATED,PR_OPEN,APPROVED}:
                        # Preserve observed effects for reconciliation without reviving this attempt.
                        self._event(conn,row['build_id'],self._now(),'publisher','late_publication',
                                    json.dumps(result),row['cancellation_generation'])
                        conn.execute('UPDATE publication_jobs SET phase=?,remote=?,lease_owner=NULL,lease_until_ns=0 WHERE attempt_id=?',
                            ('complete' if confirmed else 'cancelled', json.dumps(result), job['attempt_id']))
                        return {'status':'cancelled'}
                    state = result.get('status')
                    if state == 'merged' and not simulated:
                        if (result.get('confirmed_main') is not True
                                or any(not isinstance(result.get(k),str)
                                    or not re.fullmatch('[a-f0-9]{40}',result[k]) for k in ('merge_sha','main_sha'))):
                            result={'status':'held','reason':'merge_not_confirmed'}
                            state='held'
                    receipt = json.loads(row['receipt'])
                    receipt['publisher'] = result
                    now = self._now()
                    phase, status, hold = 'ci', PR_OPEN, None
                    if job['phase']=='publish' and state=='pending':
                        phase,status='publish',GATED
                    if state == 'merged':
                        phase,status = 'complete', SIMULATED_COMPLETE if simulated else MERGED
                    elif state == 'held':
                        phase,status,hold = 'held',HELD,'publication_blocked'
                    elif state not in {'published','pending'}:
                        phase,status,hold = 'held',HELD,'reconciliation_needed'
                    remote = result.get('pr') or job['remote']
                    conn.execute('UPDATE publication_jobs SET phase=?,remote=?,not_before_ns=?,lease_owner=NULL,lease_until_ns=0 WHERE attempt_id=?',
                                 (phase,json.dumps(remote),now+delay_ns,job['attempt_id']))
                    conn.execute('UPDATE builds SET status=?,hold_reason=?,receipt=?,updated_ns=? WHERE build_id=?',
                                 (status,hold,json.dumps(receipt),now,row['build_id']))
                    self._event(conn,row['build_id'],now,'publisher',status,json.dumps(result),job['generation'])
                    return {'status':status,'build_id':row['build_id']}
            finally:
                conn.close()

    def publication_request(self, attempt_id):
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute('SELECT request FROM publication_jobs WHERE attempt_id=?',(attempt_id,)).fetchone()
                return json.loads(row['request']) if row else None
            finally:
                conn.close()

    def resume_denied_publication(self, request):
        """Explicit retry after an unchanged, effect-free tree permission refusal.

        The trusted caller first confirms main and remote branch/PR absence by reads.
        Unknown writes, changed payloads, cancellation and active leases never resume here.
        """
        with self._lock:
            conn=self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row=conn.execute('SELECT * FROM builds WHERE attempt_id=?',(request['attempt_id'],)).fetchone()
                    job=conn.execute('SELECT * FROM publication_jobs WHERE attempt_id=?',(request['attempt_id'],)).fetchone()
                    if row is None or job is None:return False
                    prior=(json.loads(row['receipt'] or '{}').get('publisher') or {})
                    if (row['status']!=HELD or row['hold_reason']!='publication_blocked'
                            or job['phase']!='held' or job['lease_until_ns']>self._now()
                            or row['cancellation_generation']!=job['generation']
                            or row['attempt_generation']!=job['generation']
                            or json.loads(job['request'])!=request or json.loads(job['remote'])
                            or prior.get('status')!='held' or prior.get('reason')!='tree_create_failed:403'):
                        return False
                    now=self._now()
                    conn.execute("UPDATE publication_jobs SET phase='publish',not_before_ns=0,lease_owner=NULL,lease_until_ns=0 WHERE attempt_id=?",(row['attempt_id'],))
                    conn.execute('UPDATE builds SET status=?,hold_reason=NULL,updated_ns=? WHERE build_id=?',(GATED,now,row['build_id']))
                    self._event(conn,row['build_id'],now,'owner','publication_permission_retry',
                                'known_tree_refusal_after_remote_absence',row['cancellation_generation'])
                    return True
            finally:
                conn.close()

    def publication_authorized(self, attempt_id, generation, lease_owner):
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute('SELECT b.status,b.cancellation_generation,b.attempt_generation,p.lease_owner,p.lease_until_ns '
                    'FROM builds b JOIN publication_jobs p ON p.attempt_id=b.attempt_id WHERE b.attempt_id=?',
                    (attempt_id,)).fetchone()
                return bool(row and row['status'] in {GATED,PR_OPEN,APPROVED}
                    and row['cancellation_generation'] == generation == row['attempt_generation']
                    and row['lease_owner'] == lease_owner and row['lease_until_ns'] > self._now())
            finally:
                conn.close()

    def claim_review_context(self, build_id, catalog, expected_receipt_digest, lease_ns, retry_failed_review=False):
        """One explicit v1→v2 context reassessment, with no previous remote publication.

        The caller revalidates the exact base/spec/artifact before claiming. This transaction
        preserves the original rejection and fences old callbacks; it grants no approval.
        """
        from decimal import Decimal, InvalidOperation
        from .models import known
        def measured(execution):
            usage=execution.get('usage') or {}
            try:cost=Decimal(str(usage.get('cost_usd')))
            except (InvalidOperation,ValueError):return False
            return (execution.get('engine')=='flue-pi' and usage.get('complete') is True
                and cost.is_finite() and cost>=0 and type(execution.get('forwarded_count')) is int
                and execution['forwarded_count']>0)
        if type(lease_ns) is not int or not 0<lease_ns<=7200*1_000_000_000:return None
        with self._lock:
            conn=self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row=self._row(conn,build_id)
                    if (row is None or row['status']!=HELD or row['hold_reason']!='owner_review_required'
                            or not row['receipt'] or hashlib.sha256(row['receipt'].encode()).hexdigest()!=expected_receipt_digest
                            or row['attempt_generation']!=row['cancellation_generation']
                            or not catalog.matches_contract(row)
                            or catalog.missing_dependencies(row['feature_id'],self._merged_ids(conn,catalog))
                            or conn.execute('SELECT 1 FROM publication_jobs WHERE attempt_id=?',(row['attempt_id'],)).fetchone()
                            or self._rows(conn,f"WHERE status IN ({','.join('?' for _ in ACTIVE)})",tuple(ACTIVE))):
                        return None
                    receipt=json.loads(row['receipt']);circuit=receipt.get('circuit') or {}
                    execution=receipt.get('execution') or {};votes=circuit.get('votes') or []
                    context=receipt.get('review_context') or {}
                    eligible_circuit=(circuit.get('reason')=='reviewer_failed' and circuit.get('review_input_version')==2
                        and not context.get('retry_failed_review') and any(v.get('verdict')=='error' for v in votes)
                        and all(v.get('verdict') in ('approve','error') for v in votes)) if retry_failed_review else (
                        not context and circuit.get('reason')=='reviewer_rejected' and circuit.get('review_input_version',1)==1
                        and any(v.get('verdict')=='reject' for v in votes))
                    if (receipt.get('simulated') is not False or not eligible_circuit
                            or not known(receipt.get('author_model'))
                            or (receipt.get('gate') or {}).get('status')!='passed'
                            or (receipt.get('review') or {}).get('status')!='approved'
                            or circuit.get('status')!='held' or not votes
                            or not measured(execution) or execution.get('role')!='author'
                            or execution.get('build_id')!=build_id
                            or execution.get('failure') and not (
                                execution.get('failure') in ('AGENT_TIMEOUT','AGENT_DEADLINE','STEP_LIMIT','OUTPUT_LIMIT')
                                and execution.get('candidate_recovered') is True
                                and execution.get('retained_artifact_digest')==receipt.get('artifact_digest'))
                            or any(not known(v.get('model')) or not retry_failed_review
                                and not measured(v.get('execution') or {}) for v in votes)):
                        return None
                    now=self._now();generation=row['cancellation_generation']+1
                    self._event(conn,build_id,now,'supervisor','review_context_reassessment',
                        json.dumps({'previous_receipt':receipt,'previous_receipt_digest':expected_receipt_digest}),generation)
                    receipt['review_context']={'from_version':2 if retry_failed_review else 1,'to_version':2,
                        'previous_receipt_digest':expected_receipt_digest,'author_reused':True,
                        'retry_failed_review':bool(retry_failed_review)}
                    for key in ('gate','review','circuit','reason','telemetry'):
                        receipt.pop(key,None)  # Archived above; these are not results of the new pass.
                    conn.execute('UPDATE builds SET status=?,hold_reason=NULL,attempt_generation=?,cancellation_generation=?, '
                        'lease_until_ns=?,updated_ns=?,receipt=? WHERE build_id=?',
                        (DISPATCHED,generation,generation,now+lease_ns,now,json.dumps(receipt),build_id))
                    return self._row(conn,build_id)
            finally:
                conn.close()

    def attempt_authorized(self, attempt_id, generation):
        """Read-only authority check immediately before each factory model forward."""
        conn = self._connect()
        try:
            row = conn.execute('SELECT status,attempt_generation,cancellation_generation,lease_until_ns '
                               'FROM builds WHERE attempt_id=?', (attempt_id,)).fetchone()
            return bool(row and row['status'] == DISPATCHED
                and row['attempt_generation'] == generation == row['cancellation_generation']
                and row['lease_until_ns'] is not None and row['lease_until_ns'] > self._now())
        finally:
            conn.close()

    def record_preparation(self, attempt_id, generation, evidence):
        """Bind prepared metadata once; code remains in the private protected task directory."""
        from .models import known
        required = ('task_digest','spec_digest','architecture_digest','acceptance_digest')
        modern=isinstance(evidence,dict) and type(evidence.get('schema_version')) is int and evidence['schema_version']==2
        allowed = {*required,'feature_id','catalog_digest','base_sha','write_paths','preparer_model','negative_control','synthetic'}
        if modern:allowed.update(('schema_version','preparation_kind'))
        def allowed_scope(path):
            if (not isinstance(path,str) or not path or '\\' in path
                    or any(p in ('','.','..') or p.startswith('.') for p in path.rstrip('/').split('/'))):
                return False
            if not modern:
                return path.endswith('/') and path.startswith(('demo/forum-app/','demo/forum-docs/'))
            roots=('demo/forum-app/src/main/java/local/aeion/forum/',
                   'demo/forum-app/src/test/java/local/aeion/forum/',
                   'demo/forum-app/src/main/resources/','demo/forum-app/src/test/resources/',
                   'demo/forum-docs/','demo/forum-web/')
            return (path.startswith(roots)
                or path in ('knowledge/components/agora-product.md','knowledge/components/factory-architecture.md')
                or path=='demo/forum-app/build.gradle' and evidence.get('feature_id') in ('002','014'))
        static=modern and evidence.get('preparation_kind')=='registered_static_acceptance'
        model_ok=(evidence.get('preparer_model') is None and evidence.get('feature_id') in ('001','002','014')) if static else (
            isinstance(evidence,dict) and isinstance(evidence.get('preparer_model'),str) and known(evidence['preparer_model']))
        negative_ok=isinstance(evidence,dict) and (evidence.get('negative_control')=='failed_contract_assertion'
            or static and evidence.get('negative_control')=='registered_foundation_startup_rejection' and evidence.get('feature_id')=='001'
            or static and evidence.get('negative_control')=='registered_transition_source_missing' and evidence.get('feature_id') in ('002','014'))
        if (not isinstance(evidence,dict) or set(evidence) != allowed or any(not isinstance(evidence.get(k),str)
                or not re.fullmatch('[a-f0-9]{64}',evidence[k]) for k in required)
                or not model_ok or modern and evidence.get('preparation_kind') not in ('flue_prepared','registered_static_acceptance')
                or type(evidence.get('synthetic')) is not bool
                or not isinstance(evidence.get('base_sha'),str) or not re.fullmatch('[a-f0-9]{40}',evidence['base_sha'])
                or not isinstance(evidence.get('write_paths'),list) or not 1 <= len(evidence['write_paths']) <= (12 if modern else 8)
                or any(not allowed_scope(p) for p in evidence['write_paths']) or not negative_ok):
            raise StoreError('invalid_preparation_evidence')
        identity = {k:evidence[k] for k in ('feature_id','catalog_digest','spec_digest',
                                           'architecture_digest','base_sha','write_paths')}
        if hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest() != evidence['task_digest']:
            raise StoreError('preparation_digest_mismatch')
        with self._lock:
            conn=self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row=conn.execute('SELECT * FROM builds WHERE attempt_id=?',(attempt_id,)).fetchone()
                    if (row is None or row['status'] != DISPATCHED
                            or row['attempt_generation'] != generation or row['cancellation_generation'] != generation):
                        return False
                    if evidence.get('feature_id') != row['feature_id'] or evidence.get('catalog_digest') != row['catalog_digest']:
                        raise StoreError('preparation_identity_mismatch')
                    receipt=json.loads(row['receipt']) if row['receipt'] else {}
                    if receipt.get('preparation') is not None:
                        if receipt['preparation'] != evidence:raise StoreError('preparation_evidence_conflict')
                        return True
                    receipt['preparation']=evidence
                    now=self._now()
                    conn.execute('UPDATE builds SET receipt=?,updated_ns=? WHERE build_id=?',
                                 (json.dumps(receipt),now,row['build_id']))
                    self._event(conn,row['build_id'],now,'supervisor','prepared',json.dumps(evidence),generation)
                    return True
            finally:
                conn.close()

    def record_progress(self, attempt_id, generation, phase, detail):
        """Persist only bounded metadata from the currently authorized running attempt."""
        from .models import MODELS
        if not isinstance(phase, str) or phase not in PROGRESS_PHASES or not isinstance(detail, dict):
            raise StoreError('invalid_progress')
        clean = {}
        models = set(MODELS) | {'opencode-go/' + m['wire'] for m in MODELS.values()}
        if isinstance(detail.get('model'), str) and detail['model'] in models:
            clean['model'] = detail['model']
        if isinstance(detail.get('runtime'), str) and detail['runtime'] in {'flue-openshell', 'flue-local', 'flue-just-bash'}:
            clean['runtime'] = detail['runtime']
        if isinstance(detail.get('status'), str) and detail['status'] in {'passed', 'failed', 'held', 'running'}:
            clean['status'] = detail['status']
        if isinstance(detail.get('reason'),str) and re.fullmatch('[a-z][a-z0-9_]{1,95}',detail['reason']):
            clean['reason']=detail['reason']
        digest = detail.get('artifact_digest')
        if isinstance(digest, str) and re.fullmatch('[a-f0-9]{64}', digest):
            clean['artifact_digest'] = digest
        for key in ('step', 'failed_count'):
            if type(detail.get(key)) is int and 0 <= detail[key] <= 1000:
                clean[key] = detail[key]
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row = conn.execute('SELECT * FROM builds WHERE attempt_id=?', (attempt_id,)).fetchone()
                    if (row is None or row['status'] != DISPATCHED or row['attempt_generation'] != generation
                            or row['cancellation_generation'] != generation):
                        return False
                    receipt = json.loads(row['receipt']) if row['receipt'] else {}
                    previous = receipt.get('progress', {})
                    if previous.get('phase') == phase and previous.get('detail') == clean:
                        return False
                    now = self._now()
                    progress = {'phase': phase, 'detail': clean, 'time_ns': now}
                    receipt['progress'] = progress
                    if phase=='protected_check.finished':receipt['draft_check']=clean
                    conn.execute('UPDATE builds SET receipt=?, updated_ns=? WHERE build_id=?',
                                 (json.dumps(receipt), now, row['build_id']))
                    self._event(conn, row['build_id'], now, 'supervisor', 'progress',
                                json.dumps(progress), generation)
                    return True
            finally:
                conn.close()

    def complete_attempt(self, attempt_id, generation, receipt, terminal=SIMULATED_COMPLETE):
        """Finish a claimed attempt. A cancelled/stale generation cannot advance."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    row = conn.execute("SELECT * FROM builds WHERE attempt_id=?", (attempt_id,)).fetchone()
                    if row is None:
                        return {"status": "unknown_attempt"}
                    if row["attempt_generation"] != generation or row["cancellation_generation"] != generation:
                        return {"status": "stale_attempt"}
                    if row["status"] != DISPATCHED:
                        return {"status": "not_dispatched"}
                    if row['lease_until_ns'] is None or row['lease_until_ns']<=self._now():
                        return {'status':'expired_attempt'}
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
    def hold_dispatched(self, build_id, reason, actor="supervisor", receipt=None):
        """Hold the attempt without losing its identity or trusted bounded evidence."""
        if reason not in HOLD_REASONS:
            raise StoreError(f"invalid_hold_reason:{reason}")
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    row = conn.execute("SELECT * FROM builds WHERE build_id=?", (build_id,)).fetchone()
                    if row is None:
                        return {"status": "not_found"}
                    if row["status"] != DISPATCHED:
                        return {"status": "not_dispatched"}
                    now = self._now()
                    conn.execute(
                        "UPDATE builds SET status=?, hold_reason=?, receipt=COALESCE(?,receipt), lease_until_ns=NULL, updated_ns=? WHERE build_id=?",
                        (HELD, reason, json.dumps(receipt) if receipt is not None else None, now, build_id),
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
                    conn.execute("BEGIN IMMEDIATE")
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
        """Hold expired attempts: their paid/forge side effects are not known after a crash."""
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute("BEGIN IMMEDIATE")
                    now = self._now()
                    rows = conn.execute("SELECT * FROM builds WHERE status=? AND lease_until_ns < ?", (DISPATCHED, now)).fetchall()
                    for row in rows:
                        conn.execute(
                            "UPDATE builds SET status=?, hold_reason=?, lease_until_ns=NULL, updated_ns=? WHERE build_id=?",
                            (HELD, "reconciliation_needed", now, row["build_id"]),
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

    def routing_record(self, identity, cohort, detail):
        """Immutable trusted measurement; a replay may not rewrite an earlier outcome."""
        body = json.dumps(detail, sort_keys=True, separators=(',', ':'), allow_nan=False)
        if len(body.encode()) > 4096:
            raise StoreError('routing_outcome_too_large')
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    conn.execute('BEGIN IMMEDIATE')
                    row = conn.execute('SELECT detail FROM routing_outcomes WHERE identity=?', (identity,)).fetchone()
                    if row:
                        if row['detail'] != body:
                            raise StoreError('routing_outcome_conflict')
                        return False
                    conn.execute('INSERT INTO routing_outcomes VALUES (?,?,?,?)',
                                 (identity, cohort, self._now(), body))
                    return True
            finally:
                conn.close()

    def routing_read(self, cohort, limit=500):
        if type(limit) is not int or not 1 <= limit <= 500:
            raise StoreError('invalid_routing_limit')
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute('SELECT detail FROM routing_outcomes WHERE cohort=? '
                    'ORDER BY created_ns DESC, identity DESC LIMIT ?', (cohort, limit)).fetchall()
                return [json.loads(row['detail']) for row in reversed(rows)]
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
                        "catalog_digest, contract_digest, receipt, created_ns, updated_ns) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (build_id, feature_id, MERGED, f"fixture-merged-{feature_id}", "fixture", catalog.digest,
                         catalog.contracts[feature_id], json.dumps({"fixture": True, "merged_base": True}), now, now),
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
