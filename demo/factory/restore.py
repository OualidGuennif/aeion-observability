"""Disposable SQLite backup/restore drill for the factory state store.

Uses SQLite's online backup API, which is safe while WAL journals are live, then
verifies integrity, schema and row counts on the restored copy before declaring the
backup usable. This qualifies the **factory** state store only: the product's future
Postgres restore is a separate drill that requires the real product schema and is not
covered or implied by this one.
"""
import sqlite3
import sys
from pathlib import Path

EXPECTED_TABLES = ("builds", "events", "meta")


class RestoreError(ValueError):
    """A backup or restore that cannot be trusted."""


def backup_db(src, dest):
    """Copy a live SQLite database to ``dest`` through the online backup API."""
    src, dest = Path(src), Path(dest)
    if not src.is_file():
        raise RestoreError("source_missing")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    source = sqlite3.connect(src)
    target = sqlite3.connect(dest)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return dest


def verify_db(path):
    """Assert the restored copy is intact and carries the expected schema and counts."""
    path = Path(path)
    if not path.is_file():
        raise RestoreError("backup_missing")
    conn = sqlite3.connect(path)
    try:
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RestoreError(f"integrity:{integrity}")
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            missing = [t for t in EXPECTED_TABLES if t not in tables]
            if missing:
                raise RestoreError("missing_tables:" + ",".join(missing))
            return {
                "integrity": integrity,
                "tables": sorted(tables),
                "builds": conn.execute("SELECT COUNT(*) FROM builds").fetchone()[0],
                "events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                "meta": conn.execute("SELECT COUNT(*) FROM meta").fetchone()[0],
            }
        except sqlite3.DatabaseError as exc:
            raise RestoreError(f"not_a_database:{exc}") from exc
    finally:
        conn.close()


def drill(src, dest):
    """Back up ``src`` to ``dest`` and return the verified receipt of the restored copy."""
    backup_db(src, dest)
    receipt = verify_db(dest)
    receipt["source"] = str(Path(src))
    receipt["backup"] = str(Path(dest))
    return receipt


def main(argv=None):
    import json
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: python -m factory.restore_drill SRC_DB DEST_DB", file=sys.stderr)
        return 2
    try:
        print(json.dumps(drill(argv[0], argv[1]), indent=2, sort_keys=True))
    except RestoreError as exc:
        print(f"drill refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
