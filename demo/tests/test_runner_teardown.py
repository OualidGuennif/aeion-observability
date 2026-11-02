"""Sandbox teardown and budget settlement regressions for the live runner.

The sandbox and telemetry are fakes: no OpenShell workload, model or network is used.
"""
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from app import runner as runner_module
from app.runner import Runner, usage_is_complete


class FakeSpan:
    def set_attribute(self, *args, **kwargs):
        pass

    def set_status(self, *args, **kwargs):
        pass

    def end(self):
        pass


class FakeTelemetry:
    def begin(self, run):
        return FakeSpan()

    def emit(self, *args, **kwargs):
        pass


class FakeSandbox:
    instances = []

    def __init__(self, run, root, role="agent"):
        self.ref = type("Ref", (), {"id": "sandbox-fixture"})()
        self.closed = 0
        self.seed_error = None
        self.collect_error = None
        FakeSandbox.instances.append(self)

    def seed_in(self, files, root):
        if self.seed_error:
            raise self.seed_error
        return len(files)

    def sync_out(self, workspace, root):
        if self.collect_error:
            raise self.collect_error
        return 0

    def close(self):
        self.closed += 1


class FakeBudget:
    def __init__(self):
        self.settled = []

    def settle(self, reservation, actual):
        self.settled.append((reservation.id, actual))
        return Decimal("0")


class RunnerTeardownTests(unittest.TestCase):
    def setUp(self):
        FakeSandbox.instances = []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runner = Runner(FakeTelemetry(), lambda run: None, work_root=Path(self.tmp.name))
        self.patches = [
            mock.patch.object(runner_module, "Sandbox", FakeSandbox),
            mock.patch.object(Runner, "copies_out", staticmethod(lambda run: True)),
            mock.patch.object(Runner, "simulate", lambda self, run, workspace, agent: "complete"),
            mock.patch.object(Runner, "verify",
                              lambda self, run, root, workspace: {"passed": True, "failed": []}),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.run = {
            "id": "run-fixture", "status": "running", "synthetic": True, "started_ns": 0,
            "events": [], "sessions": [], "agents": 0, "human_interventions": 0,
            "postprocessing": True, "usage_complete": True, "task_id": "pricing-js-v1",
            "profile_version": "fixture", "native_cost_usd": "0", "model": "fixture/model",
            "limit": 250000, "metric": "active_context", "runtime": "flue-openshell",
            "trace_id": "trace-fixture", "root_span_id": "span-fixture", "selection": {},
        }

    def test_a_seed_failure_still_closes_the_sandbox(self):
        sandbox = FakeSandbox(self.run, Path(self.tmp.name))
        FakeSandbox.instances = []

        def construct(run, root, role="agent"):
            sandbox.seed_error = RuntimeError("fixture seed failure")
            FakeSandbox.instances.append(sandbox)
            return sandbox

        with mock.patch.object(runner_module, "Sandbox", construct):
            self.runner.run(self.run)

        self.assertEqual(sandbox.closed, 1)
        self.assertIsNone(self.runner.active_sandbox)
        self.assertEqual(self.run["status"], "failed")

    def test_a_collection_failure_still_closes_the_sandbox(self):
        sandbox = FakeSandbox(self.run, Path(self.tmp.name))
        sandbox.collect_error = ValueError("SYNC_OUT_INCOMPLETE")
        FakeSandbox.instances = []

        def construct(run, root, role="agent"):
            FakeSandbox.instances.append(sandbox)
            return sandbox

        with mock.patch.object(runner_module, "Sandbox", construct):
            self.runner.run(self.run)

        self.assertEqual(sandbox.closed, 1)
        self.assertIsNone(self.runner.active_sandbox)
        self.assertEqual(self.run["status"], "failed")

    def test_an_agent_failure_still_closes_the_sandbox(self):
        sandbox = FakeSandbox(self.run, Path(self.tmp.name))
        FakeSandbox.instances = []

        def construct(run, root, role="agent"):
            FakeSandbox.instances.append(sandbox)
            return sandbox

        def explode(self, run, workspace, agent):
            raise RuntimeError("fixture agent failure")

        with mock.patch.object(runner_module, "Sandbox", construct), \
                mock.patch.object(Runner, "simulate", explode):
            self.runner.run(self.run)

        self.assertEqual(sandbox.closed, 1)
        self.assertEqual(self.run["status"], "failed")


class RunnerSettlementTests(unittest.TestCase):
    def test_usage_completeness_requires_every_forwarded_request(self):
        self.assertTrue(usage_is_complete(2, 2))
        self.assertFalse(usage_is_complete(0, 0))
        self.assertFalse(usage_is_complete(1, 2))
        self.assertFalse(usage_is_complete(2, 2, error="UPSTREAM"))

    def setUp(self):
        self.runner = Runner(FakeTelemetry(), lambda run: None)
        self.runner.budget = FakeBudget()
        self.reservation = type("Reservation", (), {"id": "reservation-fixture"})()
        self.run = {"id": "run-fixture", "budget": {"settled_usd": None},
                    "native_cost_usd": "0", "usage_complete": False}

    def test_unknown_usage_keeps_the_reservation_open(self):
        self.runner._settle(self.run, self.reservation)
        self.assertEqual(self.runner.budget.settled, [])
        self.assertEqual(self.run["budget"]["settled_usd"], "unsettled")

    def test_complete_usage_can_settle_zero(self):
        self.run["usage_complete"] = True
        self.runner._settle(self.run, self.reservation)
        self.assertEqual(self.runner.budget.settled,
                         [("reservation-fixture", Decimal("0"))])
        self.assertEqual(self.run["budget"]["settled_usd"], "0")

    def test_a_proven_no_transport_outcome_can_release_the_reservation(self):
        self.run["budget_release"] = "proven_no_transport"
        self.runner._settle(self.run, self.reservation)
        self.assertEqual(self.runner.budget.settled,
                         [("reservation-fixture", Decimal("0"))])


if __name__ == "__main__":
    unittest.main()
