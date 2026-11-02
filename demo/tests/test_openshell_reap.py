"""The OpenShell reaper selects only old managed containers and never removes in dry-run."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "openshell"))
from reap import created_timestamp, reap, stale_ids

NOW = 1_800_000_000.0  # 2027-01-15T08:00:00Z


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


class ReapTests(unittest.TestCase):
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
        names = reap(older_than=3600, execute=False, now=NOW, docker=docker)
        self.assertEqual(names, ["old"])
        self.assertEqual(calls, [])

    def test_execute_removes_only_the_selected_container(self):
        calls = []
        docker = fake_docker(calls, {"old": 7200, "young": 600})
        names = reap(older_than=3600, execute=True, now=NOW, docker=docker)
        self.assertEqual(names, ["old"])
        self.assertEqual(calls, [("rm", "-f", "old")])


if __name__ == "__main__":
    unittest.main()
