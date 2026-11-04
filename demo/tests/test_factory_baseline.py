"""Pinned-base baselines: verified evidence, replay safety and dependency unlocking."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.baseline import BASELINE_FEATURES, verify
from factory.manifest import load_manifest
from factory.store import Store, StoreError
from factory.target import ProtectedCheck

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
    stdout = ''
    stderr = ''


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

    def test_cli_bootstrap_does_not_shadow_the_standard_queue_module(self):
        demo = Path(__file__).resolve().parents[1]
        code = ('import sys; sys.path[:0] = ' + repr([str(demo), str(demo / 'factory')])
                + '; import factory.baseline; import queue; assert hasattr(queue, "LifoQueue")')
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

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

        # A hold is never silently retried: the operator closes the old request first.
        store.cancel(held["build_ids"][0])
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
        refreshed = {**evidence, 'verified_at_ns': evidence['verified_at_ns'] + 1,
                     'check': {**evidence['check'], 'duration_ms': 42}}
        self.assertEqual(store.record_baseline('001', refreshed, catalog)['status'], 'replayed')
        changed = {**refreshed, 'paths': {**refreshed['paths'], 'other.java': 'c' * 64}}
        self.assertEqual(store.record_baseline('001', changed, catalog)['status'], 'conflict')

    def test_baseline_evidence_and_trace_remain_visible_without_becoming_a_model_build(self):
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(FIXTURE))
        catalog = load_manifest(manifest)
        store = Store(self.root / 'factory.db')
        evidence = verify('001', self.target, lambda command, **kwargs: Completed())
        recorded = store.record_baseline('001', evidence, catalog)
        receipt = json.loads(store.board()[0]['receipt'])
        self.assertEqual(receipt['base_sha'], evidence['base_sha'])
        self.assertEqual(receipt['build_id'], recorded['build_ids'][0])
        self.assertFalse(receipt['simulated'])
        store.record_baseline_trace(recorded['build_ids'][0], {'status': 'confirmed', 'trace_id': 'a' * 32})
        self.assertEqual(json.loads(store.board()[0]['receipt'])['telemetry']['status'], 'confirmed')
        self.assertEqual(store.record_baseline('001', evidence, catalog)['status'], 'replayed')
        self.assertEqual(store.board()[0]['status'], 'baseline')

    def test_a_baseline_does_not_supersede_an_active_request(self):
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(FIXTURE))
        catalog = load_manifest(manifest)
        store = Store(self.root / 'factory.db')
        store.admit(['001'], 'running-owner-request', catalog)
        evidence = verify('001', self.target, lambda command, **kwargs: Completed())
        with self.assertRaisesRegex(StoreError, 'feature_in_progress:001'):
            store.record_baseline('001', evidence, catalog)
        self.assertEqual(len(store.board()), 1)

    def test_feature_017_requires_its_external_contract_not_just_a_passing_base_suite(self):
        contract = self.root / 'Contract.java'
        contract.write_text('// external acceptance\n')
        self.target.feature_id = '017'
        self.target.protected_check = ProtectedCheck('gradle_test', ['gradle', '{repo}'], {},
            contract, 'src/test/External.java', 60)
        relative = 'demo/forum-app/src/main/java/local/aeion/forum/RequestValidationFilter.java'
        def materialize(destination):
            for relative in BASELINE_FEATURES['017']['paths']:
                path = Path(destination) / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('// validation\n')
            return self.target.base_sha
        self.target.materialize = materialize
        def runner(command, **kwargs):
            self.assertEqual((Path(kwargs['cwd']) / 'src/test/External.java').read_text(), contract.read_text())
            return Completed()
        evidence = verify('017', self.target, runner)
        self.assertEqual(evidence['check']['returncode'], 0)
        self.assertTrue(evidence['check']['contract_sha256'])

    def test_feature_017_refuses_a_different_features_target_before_running(self):
        self.target.feature_id = '013'
        runner = mock.Mock()
        with self.assertRaisesRegex(SystemExit, 'baseline_target_mismatch'):
            verify('017', self.target, runner)
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
