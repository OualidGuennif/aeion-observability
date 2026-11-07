"""The OpenShell reaper selects only old managed containers, never removes in dry-run, and holds
the sweep while a factory build lease could still own a sandbox."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "openshell"))
from reap import created_timestamp, lease_state, reap, stale_ids, sweep

NOW = 1_800_000_000.0  # 2027-01-15T08:00:00Z
NOW_NS = int(NOW * 1_000_000_000)


def stamp(seconds_ago):
    return datetime.fromtimestamp(NOW - seconds_ago, timezone.utc).isoformat().replace("+00:00", "Z")


def fake_docker(calls, ages):
    def docker(*args):
        if args[0] == "ps":
            return SimpleNamespace(stdout="\n".join(ages) + "\n")
        if args[0] == "inspect":
            container_id = args[1]
            return SimpleNamespace(stdout=json.dumps([{
                "Name": "/" + container_id,
                "Created": stamp(ages[container_id]),
            }]))
        if args[0] == "rm":
            calls.append(args)
            return SimpleNamespace(stdout="")
        raise AssertionError(args)
    return docker


def write_store(directory, rows, name="factory.db"):
    path = Path(directory) / name
    connection = sqlite3.connect(path)
    with connection:
        connection.execute("CREATE TABLE builds (build_id TEXT, status TEXT, lease_until_ns INTEGER)")
        connection.executemany("INSERT INTO builds VALUES (?,?,?)", rows)
    connection.close()
    return path


class ReapTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.directory = self._temp.name
        self.idle_store = write_store(self.directory, [("expired", "dispatched", NOW_NS - 1)])

    def test_created_timestamp_accepts_docker_rfc3339(self):
        self.assertIsNotNone(created_timestamp("2026-11-01T19:27:47.09136772Z"))
        self.assertIsNone(created_timestamp("not a timestamp"))

    def test_only_containers_older_than_the_window_are_selected(self):
        docker = fake_docker([], {"old": 7200, "young": 600})
        selected = stale_ids(["old", "young"], older_than=3600, now=NOW, docker=docker)
        self.assertEqual(selected, ["old"])

    def test_dry_run_does_not_remove_anything(self):
        calls = []
        docker = fake_docker(calls, {"old": 7200})
        names = reap(older_than=3600, execute=False, now=NOW, docker=docker, store=self.idle_store)
        self.assertEqual(names, ["old"])
        self.assertEqual(calls, [])

    def test_execute_removes_only_the_selected_container(self):
        calls = []
        docker = fake_docker(calls, {"old": 7200, "young": 600})
        names = reap(older_than=3600, execute=True, now=NOW, docker=docker, store=self.idle_store)
        self.assertEqual(names, ["old"])
        self.assertEqual(calls, [("rm", "-f", "old")])

    def test_missing_store_means_no_factory_lease_exists(self):
        missing = Path(self.directory) / "never-created.db"
        self.assertEqual(lease_state(store=missing, now=NOW), {"state": "absent", "count": 0})
        calls = []
        docker = fake_docker(calls, {"old": 7200})
        names = reap(older_than=3600, execute=True, now=NOW, docker=docker, store=missing)
        self.assertEqual(names, ["old"])
        self.assertEqual(calls, [("rm", "-f", "old")])

    def test_future_dispatched_lease_is_active_and_expired_is_idle(self):
        active = write_store(self.directory, [("live", "dispatched", NOW_NS + 1)], "active.db")
        self.assertEqual(lease_state(store=active, now=NOW)["state"], "active")
        self.assertEqual(lease_state(store=self.idle_store, now=NOW), {"state": "idle", "count": 0})

    def test_an_idle_factory_removes_a_young_orphan_pair(self):
        calls = []
        docker = fake_docker(calls, {"sandbox": 30, "sandbox-supervisor": 30})
        report = sweep(older_than=0, execute=True, now=NOW, docker=docker, store=self.idle_store)
        self.assertIsNone(report["blocked"])
        self.assertEqual(sorted(report["removed"]), ["sandbox", "sandbox-supervisor"])
        self.assertEqual(sorted(call[2] for call in calls), ["sandbox", "sandbox-supervisor"])

    def test_active_lease_holds_a_young_orphan_too(self):
        active = write_store(self.directory, [("live", "dispatched", NOW_NS + 60_000_000_000)], "young-held.db")
        calls = []
        docker = fake_docker(calls, {"sandbox": 30})
        report = sweep(older_than=0, execute=True, now=NOW, docker=docker, store=active)
        self.assertEqual(report["blocked"], "build_lease_active")
        self.assertEqual(report["removed"], [])
        self.assertEqual(calls, [])

    def test_active_lease_holds_the_sweep(self):
        active = write_store(self.directory, [("live", "dispatched", NOW_NS + 60_000_000_000)], "held.db")
        calls = []
        docker = fake_docker(calls, {"old": 7200})
        report = sweep(older_than=3600, execute=True, now=NOW, docker=docker, store=active)
        self.assertEqual(report["containers"], ["old"])
        self.assertEqual(report["blocked"], "build_lease_active")
        self.assertEqual(report["removed"], [])
        self.assertEqual(calls, [])

    def test_a_directory_in_place_of_the_store_is_not_absent(self):
        directory = Path(self.directory) / "store-is-a-directory"
        directory.mkdir()
        self.assertEqual(lease_state(store=directory, now=NOW)["state"], "unknown")
        calls = []
        docker = fake_docker(calls, {"old": 7200})
        report = sweep(older_than=3600, execute=True, now=NOW, docker=docker, store=directory)
        self.assertEqual(report["blocked"], "build_lease_unknown")
        self.assertEqual(calls, [])

    def test_unreadable_store_is_not_evidence_that_nothing_runs(self):
        corrupt = Path(self.directory) / "corrupt.db"
        corrupt.write_text("not a database", encoding="utf-8")
        self.assertEqual(lease_state(store=corrupt, now=NOW)["state"], "unknown")
        calls = []
        docker = fake_docker(calls, {"old": 7200})
        report = sweep(older_than=3600, execute=True, now=NOW, docker=docker, store=corrupt)
        self.assertEqual(report["blocked"], "build_lease_unknown")
        self.assertEqual(report["removed"], [])
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
