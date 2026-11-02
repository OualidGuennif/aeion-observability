"""Pinned-base baselines: verified evidence, replay safety and dependency unlocking."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.baseline import BASELINE_FEATURES, verify
from factory.manifest import load_manifest
from factory.store import Store

FIXTURE = {
    "schema_version": 2,
    "count": 2,
    "features": [
        {"id": "001", "title": "Skeleton", "area": "foundation", "size": "S",
         "parallel": False, "phase": "P0", "tier": 3, "write_paths": ["demo/forum/product/"],
         "depends_on": [], "file": "001.md"},
        {"id": "013", "title": "Security headers", "area": "foundation", "size": "S",
         "parallel": False, "phase": "P0", "tier": 3, "write_paths": ["demo/forum/product/"],
         "depends_on": ["001"], "file": "013.md"},
    ],
}


class FakeCheck:
    id = "gradle_test"
    timeout_seconds = 60

    def command_for(self, repo, controller):
        return ["gradle", "test", str(repo)]


class FakeTarget:
    base_sha = "a" * 40
    controller = Path("/controller")
    protected_check = FakeCheck()

    def __init__(self, root):
        self.root = root

    def materialize(self, destination):
        for relative in BASELINE_FEATURES["001"]["paths"]:
            path = Path(destination) / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        return self.base_sha


class Completed:
    returncode = 0
    qualification = {"status": "qualified", "image_id": "sha256:" + "b" * 64,
                     "probe": {"network": "denied"}}


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = FakeTarget(self.root)

    def test_verified_paths_and_isolated_test_suite_make_evidence(self):
        evidence = verify("001", self.target, lambda command, **kwargs: Completed())
        self.assertEqual(evidence["base_sha"], self.target.base_sha)
        self.assertEqual(set(evidence["paths"]), set(BASELINE_FEATURES["001"]["paths"]))
        self.assertEqual(evidence["check"]["isolation"]["status"], "qualified")

    def test_a_failed_base_suite_is_not_recorded(self):
        def runner(command, **kwargs):
            completed = Completed()
            completed.returncode = 1
            return completed

        with self.assertRaises(SystemExit):
            verify("001", self.target, runner)

    def test_a_baseline_unlocks_a_dependent_feature(self):
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(FIXTURE))
        catalog = load_manifest(manifest)
        store = Store(self.root / "factory.db")
        held = store.admit(["013"], "before", catalog)
        self.assertEqual(store.board()[0]["status"], "held")
        self.assertEqual(store.board()[0]["hold_reason"], "dependency_missing")

        evidence = verify("001", self.target, lambda command, **kwargs: Completed())
        recorded = store.record_baseline("001", evidence, catalog)
        self.assertEqual(recorded["status"], "recorded")
        self.assertIn("baseline", [row["status"] for row in store.board()])

        queued = store.admit(["013"], "after", catalog)
        self.assertEqual(queued["status"], "admitted")
        rows = [row for row in store.board() if row["feature_id"] == "013"]
        self.assertIn("queued", [row["status"] for row in rows])
        self.assertEqual(held["status"], "admitted")  # admission itself was accepted

    def test_replaying_the_same_baseline_is_idempotent(self):
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(FIXTURE))
        catalog = load_manifest(manifest)
        store = Store(self.root / "factory.db")
        evidence = verify("001", self.target, lambda command, **kwargs: Completed())
        first = store.record_baseline("001", evidence, catalog)
        second = store.record_baseline("001", evidence, catalog)
        self.assertEqual(first["status"], "recorded")
        self.assertEqual(second["status"], "replayed")


if __name__ == "__main__":
    unittest.main()
