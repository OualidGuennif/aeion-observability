"""Worker → queue → publisher, with the circuit and the credential separation in place."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.dispatch import DispatchWorker
from factory.manifest import Catalog
from factory.publish import FakeForge, Publisher
from factory.publisher import verified_receipt
from factory.store import SIMULATED_COMPLETE, Store


def feat(fid):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum/product/"], "depends_on": [], "file": f"{fid}.md",
    }


def config():
    return {"profile": "fake", "mode": "fake", "deadline_ns": 60_000_000_000,
            "step_cap": 100, "context_limit": 250_000, "cost_reservation_usd": "0.00"}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.specs = self.root / "specs"
        self.specs.mkdir()
        (self.specs / "001.md").write_text("# 001\n")
        self.cat = Catalog({"schema_version": 2, "count": 1, "features": [feat("001")]})
        self.state = self.root / "state"
        self.store = Store(self.state / "factory.db")

    def worker(self, complete=None, require_circuit=True, defer=True):
        return DispatchWorker(self.store, self.cat, self.specs, self.state / "work", config(),
                              target_repo="o/r", defer_to=self.state if defer else None,
                              review_complete=complete, require_circuit=require_circuit,
                              author_model="deepseek-4.1-flash", allow_unbudgeted=True)

    def test_worker_queues_instead_of_publishing(self):
        self.store.admit(["001"], "k1", self.cat)
        result = self.worker(lambda model, prompt: {"verdict": "approve", "reason": "ok"}).run_once()
        self.assertEqual(result["result"]["status"], "completed")
        receipt = json.loads(self.store.board()[0]["receipt"])
        self.assertEqual(receipt["circuit"]["status"], "approved")
        self.assertEqual(receipt["publisher"]["decision"], "deferred")
        self.assertEqual(len(list((self.state / "publish-queue").glob("*.json"))), 1)

    def test_the_build_brief_stops_the_agent_on_its_branch(self):
        self.store.admit(["001"], "k8", self.cat)
        self.worker(lambda model, prompt: {"verdict": "approve", "reason": "ok"}).run_once()
        build = self.store.board()[0]
        brief = (self.state / "work" / build["build_id"] / "TASK.md").read_text()
        self.assertIn("aeion/build-" + build["attempt_id"][:24], brief)
        self.assertIn("no push, no pull request, no review, no merge", brief)

    def test_no_publish_credential_is_needed_by_the_worker(self):
        self.store.admit(["001"], "k2", self.cat)
        worker = self.worker(lambda model, prompt: {"verdict": "approve", "reason": "ok"})
        worker.run_once()
        # The queued request carries no credential of any kind.
        path = next((self.state / "publish-queue").glob("*.json"))
        body = path.read_text().lower()
        self.assertNotIn("authorization", body)
        self.assertNotIn("token", body)

    def test_rejected_circuit_publishes_nothing_and_queues_one_correction(self):
        self.store.admit(["001"], "k3", self.cat)
        result = self.worker(lambda model, prompt: {"verdict": "reject", "reason": "backdoor"}).run_once()
        self.assertEqual(result["result"]["status"], "completed")
        self.assertEqual(result["result"]["correction"]["round"], 1)
        self.assertEqual([b["status"] for b in self.store.board()], ["failed", "queued"])
        self.assertEqual(list((self.state / "publish-queue").glob("*.json")), [])

    def test_unconfigured_circuit_never_publishes(self):
        self.store.admit(["001"], "k4", self.cat)
        result = self.worker(complete=None).run_once()
        self.assertEqual(result["result"]["reason"], "review_circuit_unconfigured")
        self.assertEqual(list((self.state / "publish-queue").glob("*.json")), [])

    def test_simulated_worker_receipt_is_never_publishable_to_the_real_forge(self):
        self.store.admit(["001"], "k5", self.cat)
        self.worker(lambda model, prompt: {"verdict": "approve", "reason": "ok"}).run_once()
        path = next((self.state / "publish-queue").glob("*.json"))
        request = json.loads(path.read_text())
        self.assertIsNone(verified_receipt(self.store, request))

    def test_receipt_without_circuit_approval_is_not_publishable(self):
        self.store.admit(["001"], "k6", self.cat)
        self.worker(complete=None, require_circuit=False).run_once()
        build = self.store.board()[0]
        self.assertEqual(build["status"], SIMULATED_COMPLETE)
        request = {"attempt_id": build["attempt_id"], "build_id": build["build_id"],
                   "artifact_digest": json.loads(build["receipt"])["artifact_digest"],
                   "base": json.loads(build["receipt"])["base_sha"]}
        self.assertIsNone(verified_receipt(self.store, request))

    def test_tampered_request_digest_is_not_publishable(self):
        self.store.admit(["001"], "k7", self.cat)
        self.worker(lambda model, prompt: {"verdict": "approve", "reason": "ok"}).run_once()
        request = json.loads(next((self.state / "publish-queue").glob("*.json")).read_text())
        request["artifact_digest"] = "0" * 64
        self.assertIsNone(verified_receipt(self.store, request))

    def test_tampered_queued_bytes_are_not_publishable(self):
        """Keep every receipt field, swap the content: the receipt must not certify it."""
        self.store.admit(["001"], "k9", self.cat)
        self.worker(lambda model, prompt: {"verdict": "approve", "reason": "ok"}).run_once()
        request = json.loads(next((self.state / "publish-queue").glob("*.json")).read_text())
        request["files"] = {path: "tampered\n" for path in request["files"]}
        receipt = verified_receipt(self.store, request)
        self.assertIsNone(receipt)
        forge = FakeForge()
        decision = Publisher("o/r", forge, expected_base=json.loads(
            self.store.board()[0]["receipt"])["base_sha"],
            expected_artifact_digest=json.loads(self.store.board()[0]["receipt"])["artifact_digest"]).decide(request)
        self.assertEqual(decision["decision"], "refused")
        self.assertEqual(decision["reason"], "forged_content")
        self.assertEqual(forge.published, {})


if __name__ == "__main__":
    unittest.main()
