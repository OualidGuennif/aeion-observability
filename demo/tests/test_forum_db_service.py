"""The SQLite service keeps the forum's database survivable: snapshots, drills, one writer."""
import json
import shutil
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forum-db"))
import run as service_run
from service import ServiceError, SqliteService, sha256_file, verify_copy

SCHEMA = """
CREATE TABLE settings (name TEXT PRIMARY KEY, value TEXT NOT NULL, updated_ns INTEGER NOT NULL);
CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT NOT NULL, created_ns INTEGER NOT NULL);
CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, name TEXT NOT NULL, applied_ns INTEGER NOT NULL);
"""


def make_database(path, rows=3):
    connection = sqlite3.connect(str(path))
    connection.executescript(SCHEMA)
    connection.execute("PRAGMA journal_mode=WAL")
    for index in range(rows):
        connection.execute("INSERT INTO settings(name, value, updated_ns) VALUES (?, ?, ?)",
                           ("setting.%d" % index, "value %d" % index, index))
    connection.commit()
    connection.close()
    return path


class FixedClock:
    """Every time the service records comes from here, so a drill is repeatable."""

    def __init__(self, start=1_790_000_000.0):
        self.now = start

    def __call__(self):
        self.now += 1.0
        return self.now


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.database = make_database(self.root / "agora.db")
        self.snapshots = self.root / "snapshots"
        self.clock = FixedClock()
        self.service = SqliteService(self.database, self.snapshots, keep=2, clock=self.clock)
        self.addCleanup(self.service.release_writer_lease)

    def test_integrity_reports_every_table_and_its_rows(self):
        report = self.service.integrity()
        self.assertTrue(report["ok"])
        self.assertEqual("ok", report["verdict"])
        self.assertEqual(3, report["tables"]["settings"])
        self.assertEqual(0, report["tables"]["threads"])

    def test_connect_sets_wal_and_a_busy_timeout(self):
        with self.service.session(readonly=True) as connection:
            self.assertEqual("wal", str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower())
            self.assertEqual(5000, connection.execute("PRAGMA busy_timeout").fetchone()[0])

    def test_a_missing_database_is_refused_not_created(self):
        missing = self.root / "absent.db"
        service = SqliteService(missing, self.snapshots)
        with self.assertRaises(ServiceError):
            service.integrity()
        self.assertFalse(missing.exists(), "a guardian must not create an empty database")

    def test_snapshot_is_a_verified_consistent_copy(self):
        record = self.service.snapshot(label="drill")
        self.assertTrue(Path(record["path"]).exists())
        self.assertEqual("ok", record["integrity"])
        self.assertEqual(3, record["tables"]["settings"])
        self.assertEqual(sha256_file(Path(record["path"])), record["sha256"])
        verdict = verify_copy(Path(record["path"]), expect_tables=record["tables"])
        self.assertTrue(verdict["ok"], verdict)
        self.assertEqual([], verdict["missing_tables"])
        self.assertEqual([], verdict["extra_tables"])

    def test_snapshot_label_is_validated(self):
        with self.assertRaises(ServiceError) as refusal:
            self.service.snapshot(label="../escape")
        self.assertIn("snapshot_label_invalid", str(refusal.exception))

    def test_retention_keeps_the_newest_and_reports_removals(self):
        for _ in range(4):
            self.service.snapshot(label="tick")
        removed = self.service.prune()
        self.assertEqual(2, len(removed))
        self.assertEqual(2, len(self.service.snapshots()))

    def test_restore_drill_proves_the_copy_and_leaves_the_live_file_alone(self):
        before = sha256_file(self.database)
        record = self.service.snapshot(label="drill")
        result = self.service.restore_drill(Path(record["path"]))
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["unchanged_source"])
        self.assertEqual(3, result["tables"]["settings"])
        self.assertEqual(before, sha256_file(self.database), "a drill must not write the live file")
        self.assertTrue(Path(result["restored"]).exists())

    def test_restore_drill_refuses_a_truncated_snapshot(self):
        record = self.service.snapshot(label="drill")
        broken = self.root / "broken.db"
        broken.write_bytes(Path(record["path"]).read_bytes()[:200])
        with self.assertRaises(ServiceError) as refusal:
            self.service.restore_drill(broken)
        self.assertIn("restore_unusable", str(refusal.exception))

    def test_restore_drill_accepts_an_older_snapshot_and_reports_the_lag(self):
        record = self.service.snapshot(label="older")
        connection = sqlite3.connect(str(self.database))
        connection.execute("INSERT INTO settings(name, value, updated_ns) VALUES ('late', 'row', 9)")
        connection.commit()
        connection.close()
        result = self.service.restore_drill(Path(record["path"]))
        self.assertTrue(result["ok"], result)
        self.assertEqual(1, result["lag"]["settings"], "one row was written after the snapshot")
        self.assertEqual(4, result["live_tables"]["settings"])
        self.assertEqual(3, result["tables"]["settings"])

    def test_restore_drill_refuses_a_copy_that_lost_a_table(self):
        record = self.service.snapshot(label="drill")
        damaged = self.root / "schema-drift.db"
        shutil.copyfile(record["path"], damaged)
        connection = sqlite3.connect(str(damaged))
        connection.execute("DROP TABLE threads")
        connection.commit()
        connection.close()
        with self.assertRaises(ServiceError) as refusal:
            self.service.restore_drill(damaged)
        self.assertIn("restore_unusable", str(refusal.exception))
        self.assertIn("threads", str(refusal.exception))

    def test_a_second_writer_lease_is_refused(self):
        other = SqliteService(self.database, self.snapshots, clock=self.clock)
        self.addCleanup(other.release_writer_lease)
        self.service.take_writer_lease()
        with self.assertRaises(ServiceError) as refusal:
            other.take_writer_lease()
        self.assertIn("writer_lease_held", str(refusal.exception))
        self.assertTrue(self.service.release_writer_lease())
        other.take_writer_lease()

    def test_snapshot_stays_consistent_while_a_writer_keeps_going(self):
        stop = threading.Event()
        written = {"count": 0}

        def writer():
            connection = sqlite3.connect(str(self.database), timeout=5.0)
            index = 0
            while not stop.is_set():
                connection.execute("INSERT INTO settings(name, value, updated_ns) VALUES (?, ?, ?)",
                                   ("live.%d" % index, "x", index))
                connection.commit()
                index += 1
                written["count"] = index
            connection.close()

        thread = threading.Thread(target=writer, daemon=True)
        thread.start()
        try:
            records = [self.service.snapshot(label="concurrent") for _ in range(3)]
        finally:
            stop.set()
            thread.join(timeout=5)
        self.assertGreater(written["count"], 0, "the writer must actually have written")
        for record in records:
            self.assertEqual("ok", record["integrity"])
            verdict = verify_copy(Path(record["path"]))
            self.assertTrue(verdict["ok"], verdict)
            self.assertIn("settings", verdict["tables"])


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.database = make_database(self.root / "agora.db")
        self.service = SqliteService(self.database, self.root / "snapshots",
                                     keep=2, clock=FixedClock())
        self.server = service_run.make_server(self.service, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        host, port = self.server.server_address
        self.base = "http://%s:%d" % (host, port)

    def stop(self):
        self.service.release_writer_lease()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def get(self, route):
        with urllib.request.urlopen(self.base + route, timeout=5) as response:
            return response.status, json.loads(response.read())

    def post(self, route, payload=None):
        body = json.dumps(payload or {}).encode()
        request = urllib.request.Request(self.base + route, data=body,
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())

    def test_healthz_passes_quick_check(self):
        status, body = self.get("/healthz")
        self.assertEqual(200, status)
        self.assertEqual("ok", body["status"])
        self.assertEqual(3, body["tables"]["settings"])

    def test_stats_names_the_journal_and_the_wal(self):
        status, body = self.get("/v1/stats")
        self.assertEqual(200, status)
        self.assertEqual("wal", body["journal_mode"].lower())
        self.assertEqual("ok", body["integrity"])
        self.assertIn("wal_bytes", body)

    def test_snapshot_then_drill_over_http(self):
        status, body = self.post("/v1/snapshot", {"label": "http"})
        self.assertEqual(201, status)
        self.assertEqual("ok", body["integrity"])
        status, listing = self.get("/v1/snapshots")
        self.assertEqual(200, status)
        self.assertEqual(1, len(listing["snapshots"]))
        status, drill = self.post("/v1/restore-drill", {"snapshot": body["path"]})
        self.assertEqual(200, status)
        self.assertTrue(drill["ok"])

    def test_unknown_route_is_a_404_with_a_code(self):
        with self.assertRaises(urllib.error.HTTPError) as failure:
            self.get("/v1/nope")
        self.assertEqual(404, failure.exception.code)
        failure.exception.close()

    def test_a_bad_label_is_a_400_and_a_body_cap_is_a_413(self):
        with self.assertRaises(urllib.error.HTTPError) as failure:
            self.post("/v1/snapshot", {"label": "not allowed"})
        self.assertEqual(400, failure.exception.code)
        failure.exception.close()
        oversized = urllib.request.Request(
            self.base + "/v1/snapshot", data=b"x" * 5000,
            headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as too_big:
            urllib.request.urlopen(oversized, timeout=5)
        self.assertEqual(413, too_big.exception.code)
        too_big.exception.close()

    def test_healthz_answers_503_when_the_file_is_gone(self):
        self.stop()
        self.database.unlink()
        self.service = SqliteService(self.database, self.root / "snapshots", clock=FixedClock())
        status, body = service_run.health(self.service)
        self.assertEqual(503, status)
        self.assertEqual("unavailable", body["status"])


if __name__ == "__main__":
    unittest.main()
