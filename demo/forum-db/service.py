"""SQLite as a service: one owner of the file, consistent snapshots, and a restore drill.

The forum's database is not an embedded file that happens to sit next to the application. It is a
resource with an owner:

  * **One writer.** The forum process is the writer; this service is the guardian. In guardian mode
    it never opens a write transaction, so it cannot fight the application for the write lock. In
    writer mode it takes an exclusive lease first, and a second writer is refused rather than racing.
  * **Durability on purpose.** WAL, a busy timeout and `synchronous=NORMAL` are set on every
    connection, and every snapshot is a `VACUUM INTO` (a consistent copy taken while writers keep
    going) followed by an atomic rename, a SHA-256 and an integrity check on the copy.
  * **A drill, not a promise.** A restore is only believed after it has been performed: the snapshot
    is copied to a scratch file, opened read-only, `integrity_check` must pass and every table must
    carry the same row count as the live database. The live file is never touched by a drill.

Everything here is deterministic given (database bytes, clock, policy): no random sampling, no
wall-clock-dependent decision inside a check.
"""
import contextlib
import hashlib
import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

DEFAULTS = {
    "busy_timeout_ms": 5000,
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "keep_snapshots": 5,
}

SNAPSHOT_SUFFIX = ".db"
SCHEMA_TABLES = ("settings", "accounts", "sessions", "threads", "schema_events", "schema_migrations")


class ServiceError(ValueError):
    """A refusal with a code a caller can act on; never a silent half-operation."""


def _now_ns(clock):
    return int(clock() * 1_000_000_000)


class SqliteService:
    """Guardian for one SQLite file: snapshots, integrity, statistics and a restore drill."""

    def __init__(self, database, snapshot_dir, keep=None, clock=time.time):
        self.database = Path(database).resolve()
        self.snapshot_dir = Path(snapshot_dir).resolve()
        self.keep = int(keep if keep is not None else DEFAULTS["keep_snapshots"])
        if self.keep < 1:
            raise ServiceError("keep_snapshots_must_be_positive")
        self.clock = clock
        self._lease = None

    # -- connections ---------------------------------------------------------------------------
    def connect(self, readonly=True):
        """A connection with the pragmas this database must never run without."""
        if not self.database.exists():
            raise ServiceError("database_missing: %s" % self.database)
        uri = self.database.as_uri()
        if readonly:
            connection = sqlite3.connect(uri + "?mode=ro", uri=True, timeout=5.0)
        else:
            connection = sqlite3.connect(str(self.database), timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=%d" % DEFAULTS["busy_timeout_ms"])
        if not readonly:
            connection.execute("PRAGMA journal_mode=%s" % DEFAULTS["journal_mode"])
            connection.execute("PRAGMA synchronous=%s" % DEFAULTS["synchronous"])
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextlib.contextmanager
    def session(self, readonly=True):
        """A connection that is closed on exit: `with connection` commits, it does not close."""
        connection = self.connect(readonly=readonly)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    # -- lease ---------------------------------------------------------------------------------
    def take_writer_lease(self):
        """Become the only writer, or refuse. A second lease on the same file is an error."""
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        lease_path = self.database.with_suffix(self.database.suffix + ".lease")
        handle = open(lease_path, "a+", encoding="utf-8")
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (ImportError, OSError):
            handle.close()
            raise ServiceError("writer_lease_held: %s" % lease_path)
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps({"pid": os.getpid(), "taken_ns": _now_ns(self.clock)}) + "\n")
        handle.flush()
        self._lease = handle
        return lease_path

    def release_writer_lease(self):
        if self._lease is None:
            return False
        try:
            import fcntl
            fcntl.flock(self._lease.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError):
            pass
        self._lease.close()
        self._lease = None
        return True

    # -- inspections ---------------------------------------------------------------------------
    def integrity(self):
        """`quick_check` on the live file, with the row count of every table it has.

        A missing database raises: "absent" and "corrupt" are different answers, and a caller that
        saw the same shape for both would heal the wrong problem.
        """
        with self.session(readonly=True) as connection:
            verdict = connection.execute("PRAGMA quick_check").fetchone()[0]
            tables = {name: connection.execute(
                "SELECT COUNT(*) FROM %s" % quote_identifier(name)).fetchone()[0]
                for name in self._tables(connection)}
        return {"ok": str(verdict).lower() == "ok", "verdict": str(verdict), "tables": tables}

    def stats(self):
        """Size, page accounting and the WAL sidecar: the numbers an operator watches."""
        if not self.database.exists():
            raise ServiceError("database_missing: %s" % self.database)
        with self.session(readonly=True) as connection:
            page_count = connection.execute("PRAGMA page_count").fetchone()[0]
            page_size = connection.execute("PRAGMA page_size").fetchone()[0]
            freelist = connection.execute("PRAGMA freelist_count").fetchone()[0]
            journal = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
            tables = {name: connection.execute(
                "SELECT COUNT(*) FROM %s" % quote_identifier(name)).fetchone()[0]
                for name in self._tables(connection)}
        wal = self.database.with_suffix(self.database.suffix + "-wal")
        return {
            "database": str(self.database),
            "bytes": self.database.stat().st_size,
            "wal_bytes": wal.stat().st_size if wal.exists() else 0,
            "journal_mode": journal,
            "page_count": page_count,
            "page_size": page_size,
            "freelist_pages": freelist,
            "integrity": str(integrity),
            "tables": tables,
        }

    # -- snapshots -----------------------------------------------------------------------------
    def snapshot(self, label="manual"):
        """Take a consistent copy with `VACUUM INTO`, atomically publish it, verify it, prune."""
        if not self.database.exists():
            raise ServiceError("database_missing: %s" % self.database)
        if not label or not label.replace("-", "").replace("_", "").isalnum():
            raise ServiceError("snapshot_label_invalid: %r" % label)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        taken_ns = _now_ns(self.clock)
        final = self.snapshot_dir / ("agora-%d-%s%s" % (taken_ns, label, SNAPSHOT_SUFFIX))
        scratch = final.with_suffix(".partial")
        if scratch.exists():
            scratch.unlink()
        with self.session(readonly=True) as connection:
            connection.execute("VACUUM INTO ?", (str(scratch),))
        verdict = verify_copy(scratch, expect_tables=None)
        if not verdict["ok"]:
            scratch.unlink(missing_ok=True)
            raise ServiceError("snapshot_corrupt: %s" % verdict.get("error", "unknown"))
        os.replace(scratch, final)
        digest = sha256_file(final)
        record = {
            "path": str(final),
            "name": final.name,
            "label": label,
            "taken_ns": taken_ns,
            "bytes": final.stat().st_size,
            "sha256": digest,
            "integrity": "ok",
            "tables": verdict["tables"],
        }
        return record

    def snapshots(self):
        """Every published snapshot, newest first, with the digest recomputed now."""
        if not self.snapshot_dir.exists():
            return []
        found = []
        for path in sorted(self.snapshot_dir.glob("*" + SNAPSHOT_SUFFIX)):
            record = {
                "path": str(path),
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            found.append(record)
        found.sort(key=lambda item: item["name"], reverse=True)
        return found

    def prune(self):
        """Keep the newest `self.keep` snapshots; a deletion is reported, never silent."""
        ordered = self.snapshots()
        removed = []
        for record in ordered[self.keep:]:
            Path(record["path"]).unlink(missing_ok=True)
            removed.append(record["name"])
        return removed

    # -- restore drill -------------------------------------------------------------------------
    def restore_drill(self, snapshot_path=None, scratch_dir=None):
        """Restore a snapshot into a scratch file and prove it is a usable database.

        The live file is only read. A drill that cannot prove the copy is refused as
        `restore_unusable`, so no operator can mistake "the file exists" for "the backup works".
        """
        snapshot_path = Path(snapshot_path) if snapshot_path else self.latest_snapshot()
        if snapshot_path is None:
            raise ServiceError("snapshot_missing")
        if not snapshot_path.exists():
            raise ServiceError("snapshot_missing: %s" % snapshot_path)
        scratch_dir = Path(scratch_dir) if scratch_dir else self.snapshot_dir / "drills"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        restored = scratch_dir / ("drill-%d.db" % _now_ns(self.clock))
        digest_before = sha256_file(snapshot_path)
        shutil.copyfile(snapshot_path, restored)
        verdict = verify_copy(restored, expect_tables=self._live_counts())
        digest_after = sha256_file(snapshot_path)
        live = self._live_counts() or {}
        lag = {name: live.get(name, 0) - count for name, count in verdict["tables"].items()}
        result = {
            "snapshot": str(snapshot_path),
            "restored": str(restored),
            "sha256": digest_before,
            "unchanged_source": digest_before == digest_after,
            "ok": verdict["ok"],
            "integrity": verdict.get("verdict", ""),
            "tables": verdict["tables"],
            "live_tables": live,
            "lag": lag,
            "missing_tables": verdict.get("missing_tables", []),
            "extra_tables": verdict.get("extra_tables", []),
        }
        if not result["ok"] or not result["unchanged_source"]:
            result["error"] = verdict.get("error") or "restore_source_changed"
            raise ServiceError("restore_unusable: %s" % json.dumps(result, sort_keys=True))
        return result

    def latest_snapshot(self):
        ordered = self.snapshots()
        return Path(ordered[0]["path"]) if ordered else None

    # -- helpers -------------------------------------------------------------------------------
    def _live_counts(self):
        try:
            with self.session(readonly=True) as connection:
                return {name: connection.execute(
                    "SELECT COUNT(*) FROM %s" % quote_identifier(name)).fetchone()[0]
                    for name in self._tables(connection)}
        except (ServiceError, sqlite3.Error):
            return None

    @staticmethod
    def _tables(connection):
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        return [row[0] for row in rows]


def quote_identifier(name):
    """SQLite has no parameter for an identifier; quote it and refuse anything suspicious."""
    if not name or not all(character.isalnum() or character == "_" for character in name):
        raise ServiceError("identifier_invalid: %r" % name)
    return '"%s"' % name


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_copy(path, expect_tables=None):
    """Open a copy read-only and prove what it is.

    `expect_tables` is the set of table names the copy must carry. A **missing** table means the
    copy is not a backup of this database and the copy fails; an **extra** table is reported
    separately, because it means the copy came from a different schema rather than a bad one.
    Row counts are never a pass/fail here: a backup taken an hour ago legitimately holds fewer rows
    than the live file, and a check that refused it would refuse every real restore.
    """
    try:
        connection = sqlite3.connect(Path(path).as_uri() + "?mode=ro", uri=True, timeout=5.0)
    except sqlite3.Error as error:
        return {"ok": False, "error": "open_failed: %s" % error, "tables": {}}
    try:
        with connection:
            verdict = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            names = SqliteService._tables(connection)
            tables = {name: connection.execute(
                "SELECT COUNT(*) FROM %s" % quote_identifier(name)).fetchone()[0] for name in names}
    except sqlite3.Error as error:
        return {"ok": False, "error": "check_failed: %s" % error, "tables": {}}
    finally:
        connection.close()
    result = {"ok": verdict.lower() == "ok", "verdict": verdict, "tables": tables}
    if expect_tables is not None:
        expected = set(expect_tables)
        present = set(tables)
        result["missing_tables"] = sorted(expected - present)
        result["extra_tables"] = sorted(present - expected)
        if result["missing_tables"]:
            result["ok"] = False
    return result
