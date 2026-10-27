"""Tier 1 triage: frozen synthetic answers, deterministic verdict and a sandbox-free supervisor path."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import triage
try:
    from runner import TRIAGE, Runner, tasks
    IMPORTABLE = True
except ModuleNotFoundError:
    IMPORTABLE = False

TASK = "webhook-triage-v1"


def reference(events):
    # Independent reading of the contract rules; the fixture's expected answers must match it.
    first, results = {}, []
    for event in events:
        duplicate_of = first.setdefault(event["delivery_id"], event["id"])
        duplicate_of = None if duplicate_of == event["id"] else duplicate_of
        failed = event["type"].endswith(".failed")
        if event["environment"] != "production" or duplicate_of:
            severity = "low"
        elif failed and event["error_rate_pct"] >= 5:
            severity = "critical"
        else:
            severity = "high" if failed else "low"
        results.append({"id": event["id"], "severity": severity,
                        "component": {"payment": "payments", "shipment": "shipping", "login": "auth"}[event["type"].split(".")[0]],
                        "route": {"critical": "page-oncall", "high": "ticket", "low": "ignore"}[severity],
                        "duplicate_of": duplicate_of})
    return results


class FakeSpan:
    def set_attribute(self, *_args):
        pass

    def end(self):
        pass


class FakeTelemetry:
    def begin(self, run):
        run.update(trace_id="1" * 32, root_span_id="2" * 16)
        return FakeSpan()

    def emit(self, *_args, **_attrs):
        pass


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / triage.ARTIFACT

    def verdict(self, value):
        self.path.write_text(value if isinstance(value, str) else json.dumps(value))
        return triage.check(self.path, TASK)

    def test_fixture_is_synthetic_and_matches_the_contract_rules(self):
        task = triage.TRIAGE[TASK]
        self.assertIs(task["synthetic"], True)
        self.assertEqual(task["expected"], reference(task["events"]))
        for field in ("severity", "component", "route"):
            self.assertEqual({item[field] for item in task["expected"]}, set(task["labels"][field]))
        self.assertIn("submit_triage", triage.contract(TASK))

    def test_expected_answers_never_reach_the_harness(self):
        value = json.loads(triage.agent_input(TASK))
        self.assertEqual(set(value), {"labels", "events"})
        self.assertNotIn("severity", json.dumps(value["events"]))

    def test_verdict_counts_each_event(self):
        self.assertEqual(self.verdict(triage.solution(TASK)), {"passed": 8, "failed": [], "total": 8})
        self.assertEqual(self.verdict(triage.EMPTY)["passed"], 0)
        partial = json.loads(triage.solution(TASK))
        partial["results"][3]["duplicate_of"] = None
        del partial["results"][7]
        self.assertEqual(self.verdict(partial), {"passed": 6, "failed": ["evt-004", "evt-008"], "total": 8})

    def test_malformed_results_are_invalid(self):
        good = json.loads(triage.solution(TASK))["results"]
        cases = ["not json", [], {"results": good, "extra": 1}, {"results": [dict(good[0], note="x")]},
                 {"results": [dict(good[0], id="evt-999")]}, {"results": [good[0], good[0]]}, {"results": [1]}]
        for value in cases:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "INVALID_ARTIFACT"):
                self.verdict(value)
        self.path.unlink()
        os.symlink(Path(self.folder.name) / "elsewhere.json", self.path)
        with self.assertRaisesRegex(ValueError, "INVALID_ARTIFACT"):
            triage.check(self.path, TASK)

    @unittest.skipUnless(IMPORTABLE, "controller requirements required")
    def test_tasks_follow_the_runtime(self):
        self.assertEqual(list(tasks(TRIAGE)), [TASK])
        self.assertIn("pricing-js-v1", tasks("flue-local"))
        self.assertNotIn(TASK, tasks("flue-openshell"))

    @unittest.skipUnless(IMPORTABLE, "controller requirements required")
    def test_simulated_triage_hands_over_and_passes_without_any_sandbox(self):
        saved = []
        runner = Runner(FakeTelemetry(), saved.append, work_root=Path(self.folder.name))
        run = {"id": "a" * 32, "synthetic": True, "runtime": TRIAGE, "task_id": TASK, "metric": "active_context",
               "limit": 250000, "events": [], "sessions": [], "agents": 0, "native_cost_usd": "0", "status": "running"}
        with mock.patch("runner.time.sleep"), mock.patch("runner.Sandbox", side_effect=AssertionError("no sandbox")):
            runner.run(run)
        names = [event["name"] for event in run["events"]]
        self.assertEqual(run["status"], "passed", run.get("failure"))
        self.assertEqual((run["agents"], run["check"]["passed"]), (2, 8))
        self.assertIn("agent.handover", names)
        self.assertNotIn("sandbox.ready", names)
        handover = (Path(self.folder.name) / run["id"] / "workspace/HANDOVER.md").read_text()
        self.assertIn("`result.json`", handover)
        self.assertFalse((Path(self.folder.name) / "published").exists())


if __name__ == "__main__":
    unittest.main()
