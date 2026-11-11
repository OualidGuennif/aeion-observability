import json
import tempfile
from decimal import Decimal
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import Store, SIMULATED_COMPLETE, HELD, FAILED
from factory.dispatch import DispatchWorker
from factory.gateway import Gateway, SessionError


def feat(fid, depends_on=(), write=None):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": write or ["demo/forum/product/"], "depends_on": list(depends_on), "file": f"{fid}.md",
    }


def config():
    return {"profile": "fake", "mode": "fake", "deadline_ns": 60_000_000_000,
            "step_cap": 100, "context_limit": 250_000, "cost_reservation_usd": "0.00"}


class DispatchWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cat = Catalog({"schema_version": 2, "count": 1, "features": [feat("001")]})
        self.spec_dir = Path(self.tmp.name) / "specs"
        self.spec_dir.mkdir()
        (self.spec_dir / "001.md").write_text("# 001\n")
        self.store = Store(Path(self.tmp.name) / "factory.db")
        self.worker = DispatchWorker(self.store, self.cat, self.spec_dir, Path(self.tmp.name) / "work",
                                     config(), allow_unbudgeted=True)

    def test_run_once_freezes_and_completes_simulated(self):
        self.store.admit(["001"], "k1", self.cat)
        result = self.worker.run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], SIMULATED_COMPLETE)
        receipt = json.loads(build["receipt"])
        self.assertTrue(receipt["pr_shaped"])
        self.assertTrue(receipt["simulated"])
        self.assertIn("frozen_digest", receipt)
        self.assertIn("artifact_digest", receipt)
        self.assertTrue(receipt["base_sha"])

    def test_missing_spec_holds_qualification(self):
        (self.spec_dir / "001.md").unlink()
        self.store.admit(["001"], "k2", self.cat)
        result = self.worker.run_once()
        self.assertEqual(result["result"]["status"], "held")
        build = self.store.board()[0]
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "qualification_missing")

    def test_builder_failure_keeps_frozen_identity_and_exact_execution_diagnostics(self):
        class FailingBuilder:
            paid=False
            last_execution=None
            def __call__(self,repo,frozen,feature,brief):
                self.last_execution={'build_id':frozen.build_id,'failure':'CLI_STARTUP_FAILED',
                    'process_exit_code':1,'forwarded_count':0,'trace_id':'a'*32,
                    'check':{'status':'failed','reason':'product_unit_tests_failed',
                             'failed_tests':['DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED']}}
                raise ValueError('CLI_STARTUP_FAILED')
        self.worker.builder=FailingBuilder()
        self.store.admit(['001'],'startup-failure',self.cat)
        self.worker.run_once()
        row=self.store.board()[0];receipt=json.loads(row['receipt'])
        self.assertEqual(row['status'],FAILED)
        self.assertEqual(receipt['error'],'CLI_STARTUP_FAILED')
        self.assertEqual(receipt['execution']['forwarded_count'],0)
        self.assertEqual(receipt['execution']['process_exit_code'],1)
        self.assertEqual(receipt['execution']['failure'],'CLI_STARTUP_FAILED')
        self.assertEqual(receipt['execution']['check']['status'],'failed')
        self.assertEqual(len(receipt['frozen_digest']),64)
        self.assertEqual(len(receipt['base_sha']),40)

    def test_settle_releases_reservation_on_incomplete_usage(self):
        from factory.budget import DailyBudget
        b = DailyBudget(Path(self.tmp.name) / "ledger.jsonl")
        self.worker.budget, self.worker.budget_scope = b, "aeion-autonomous-forum"
        res = b.admit("aeion-autonomous-forum", "50.00", note="test-build:001")
        self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("100.00"))
        self.worker.last_usage = {"complete": False, "cost_usd": None, "estimated_cost_usd": "0.15"}
        self.worker._settle(res, {"build_id": "test-build"})
        self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("149.85"))

    def test_orphan_reservations_are_reconciled(self):
        from factory.budget import DailyBudget
        b = DailyBudget(Path(self.tmp.name) / "ledger.jsonl")
        self.worker.budget, self.worker.budget_scope = b, "aeion-autonomous-forum"
        b.admit("aeion-autonomous-forum", "50.00", note="dead-build:001")
        self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("100.00"))
        self.worker._reconcile_orphan_reservations()
        self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("150.00"))


class DispatchSessionTests(unittest.TestCase):
    """No agent holds a GitHub key: the worker mints a session, records its id, and revokes it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.cat = Catalog({"schema_version": 2, "count": 1, "features": [feat("001")]})
        self.spec_dir = root / "specs"
        self.spec_dir.mkdir()
        (self.spec_dir / "001.md").write_text("# 001\n")
        self.store = Store(root / "factory.db")
        self.audit = root / "audit.jsonl"
        self.gateway = Gateway(self.store, lambda *a: (200, {}), "OualidGuennif/aeion-autonomous-forum",
                               clock=lambda: 1_700_000_000_000_000_000, audit_path=self.audit)
        self.worker = DispatchWorker(self.store, self.cat, self.spec_dir, root / "work", config(),
                                     gateway=self.gateway, allow_unbudgeted=True)

    def test_the_attempt_gets_a_session_that_is_recorded_and_revoked(self):
        self.store.admit(["001"], "k1", self.cat)
        result = self.worker.run_once()
        self.assertEqual(result["result"]["status"], "completed")
        receipt = json.loads(self.store.board()[0]["receipt"])
        evidence = receipt["agent_session"]
        self.assertTrue(evidence["session"])
        self.assertEqual(["github:read"], evidence["capabilities"])
        self.assertNotIn("token", evidence, "a receipt must never carry the token")
        self.assertNotIn("aeion_", json.dumps(receipt), "no token text anywhere in the receipt")
        events = [json.loads(line) for line in self.audit.read_text().splitlines() if line.strip()]
        self.assertEqual(["issued", "revoked"], [event["event"] for event in events])
        self.assertEqual(events[0]["session"], evidence["session"])
        self.assertEqual("build_finished", events[1]["reason"])

    def test_a_gateway_refusal_holds_the_build_instead_of_building_it(self):
        class BrokenGateway(Gateway):
            def issue(self, *args, **kwargs):
                raise SessionError("unknown_capability:github:admin")

        worker = DispatchWorker(self.store, self.cat, self.spec_dir, Path(self.tmp.name) / "work",
                                config(), gateway=BrokenGateway(
                                    self.store, lambda *a: (200, {}), "repo/x"),
                                allow_unbudgeted=True)
        self.store.admit(["001"], "k2", self.cat)
        result = worker.run_once()
        self.assertEqual(result["result"]["status"], "held")
        self.assertEqual("credential_unavailable", result["result"]["reason"])
        build = self.store.board()[0]
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "credential_unavailable")


if __name__ == "__main__":
    unittest.main()
