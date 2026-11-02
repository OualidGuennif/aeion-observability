import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.checks import DEFAULT_CHECKS, ProtectedChecks
from factory.dispatch import DispatchWorker
from factory.manifest import Catalog
from factory.publish import FakeForge
from factory.store import FAILED, HELD, SIMULATED_COMPLETE, Store


def feat(fid, write=None):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": write or ["demo/forum/product/"], "depends_on": [], "file": f"{fid}.md",
    }


def config():
    return {"profile": "fake", "mode": "fake", "deadline_ns": 60_000_000_000,
            "step_cap": 100, "context_limit": 250_000, "cost_reservation_usd": "0.00"}


class AlwaysUncertainForge(FakeForge):
    def publish(self, request):
        super().publish(request)
        return {"status": "uncertain", "attempt_id": request["attempt_id"]}


class S3GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.spec_dir = self.root / "specs"
        self.spec_dir.mkdir()
        (self.spec_dir / "001.md").write_text("# 001\n")

    def _worker(self, write=None, checks=None, required=None, forge=None):
        self.cat = Catalog({"schema_version": 2, "count": 1,
                            "features": [feat("001", write)]})
        self.store = Store(self.root / f"factory-{id(self)}.db")
        return DispatchWorker(self.store, self.cat, self.spec_dir, self.root / "work",
                              config(), checks=checks, required_checks=required, forge=forge)

    def test_happy_path_records_gate_and_publisher_evidence(self):
        worker = self._worker()
        self.store.admit(["001"], "k1", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], SIMULATED_COMPLETE)
        receipt = json.loads(build["receipt"])
        self.assertTrue(receipt["simulated"])
        self.assertEqual(receipt["gate"]["status"], "passed")
        self.assertEqual(receipt["gate"]["results"]["scope"]["status"], "passed")
        self.assertEqual(receipt["gate"]["results"]["spec_unchanged"]["status"], "passed")
        self.assertEqual(receipt["publisher"]["decision"], "published")
        self.assertTrue(receipt["publisher"]["forge"]["pr"]["merged"])

    def test_sensitive_scope_holds_for_owner_review(self):
        worker = self._worker(write=["demo/forum/product/auth/"])
        self.store.admit(["001"], "k2", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "held")
        self.assertEqual(result["result"]["reason"], "owner_review_required")
        build = self.store.board()[0]
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "owner_review_required")

    def test_missing_required_check_holds_qualification(self):
        worker = self._worker(required=["scope", "not_registered"])
        self.store.admit(["001"], "k3", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "held")
        self.assertEqual(result["result"]["reason"], "qualification_missing")
        self.assertEqual(self.store.board()[0]["hold_reason"], "qualification_missing")

    def test_failed_check_fails_the_build(self):
        def failing(frozen, artifact_verdict):
            return False, "always_fails"
        checks = ProtectedChecks(dict(DEFAULT_CHECKS, failing=failing))
        worker = self._worker(checks=checks, required=["scope", "failing"])
        self.store.admit(["001"], "k4", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], FAILED)
        receipt = json.loads(build["receipt"])
        self.assertEqual(receipt["gate"]["status"], "failed")
        self.assertNotIn("publisher", receipt)

    def test_uncertain_forge_is_reconciled_not_redone(self):
        forge = AlwaysUncertainForge()
        worker = self._worker(forge=forge)
        self.store.admit(["001"], "k5", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], SIMULATED_COMPLETE)
        receipt = json.loads(build["receipt"])
        self.assertEqual(receipt["publisher"]["decision"], "reconciled")
        self.assertEqual(len(forge.published), 1)

    def test_review_hold_stops_a_secret_before_the_publisher(self):
        worker = self._worker()

        def write_secret(repo, frozen, feature):
            target = repo / frozen.write_scopes[0] / "secret.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("const k = 'ghp_" + "a" * 30 + "';\n")

        worker._write_simulated_impl = write_secret
        self.store.admit(["001"], "k6", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "held")
        self.assertEqual(result["result"]["reason"], "owner_review_required")
        build = self.store.board()[0]
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "owner_review_required")
        self.assertFalse(any(b.get("receipt") for b in self.store.board()))

    def test_review_refusal_fails_the_build(self):
        worker = self._worker()
        worker._write_simulated_impl = lambda repo, frozen, feature: None
        self.store.admit(["001"], "k7", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], FAILED)
        self.assertEqual(json.loads(build["receipt"])["review"]["status"], "refused")


if __name__ == "__main__":
    unittest.main()
