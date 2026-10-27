import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from kpis import summarize
from memory import analysis
from audit import Audit


def run(synthetic=False, status="passed", cost="0.02", human=0):
    return {"id": "a" * 32, "model": "opencode-go/glm-5.3-flash", "synthetic": synthetic,
            "metric": "active_context", "limit": 250000, "started_ns": 1000000000, "ended_ns": 3000000000,
            "status": status, "native_cost_usd": cost, "human_interventions": human, "agents": 1,
            "usage_complete": True,
            "check": {"passed": 12, "failed": [], "total": 12},
            "events": [{"name": "gen_ai.request", "gen_ai.usage.input_tokens": 5000, "gen_ai.usage.output_tokens": 500}]}


class EvidenceTests(unittest.TestCase):
    def test_failed_costs_and_human_assistance_count(self):
        rows = summarize([run(), run(status="failed", cost="0.01"), run(human=1)])
        self.assertEqual(rows[0]["autonomous"], 1)
        self.assertEqual(rows[0]["completed"], 3)
        self.assertEqual(rows[0]["cost_per_autonomous_success_usd"], "0.05")
        self.assertEqual(rows[0]["input_tokens"], 15000)

    def test_no_success_is_undefined(self):
        self.assertIsNone(summarize([run(status="failed")])[0]["cost_per_autonomous_success_usd"])

    def test_unknown_usage_does_not_create_a_zero_cost_winner(self):
        pending = run(status="failed", cost="0")
        pending["usage_complete"] = False
        self.assertIsNone(summarize([run(), pending])[0]["cost_per_autonomous_success_usd"])

    def test_interrupted_run_is_unresolved_not_pending(self):
        stopped = run(status="interrupted")
        del stopped["ended_ns"]
        row = summarize([run(), stopped])[0]
        self.assertEqual((row["interrupted"], row["pending"], row["completed"]), (1, 0, 1))
        self.assertFalse(row["usage_complete"])
        self.assertIsNone(row["cost_per_autonomous_success_usd"])

    def test_synthetic_and_gate_profiles_are_not_pooled(self):
        other = run()
        other["limit"] = 12000
        self.assertEqual(len(summarize([run(), run(synthetic=True), other])), 3)

    def test_execution_tiers_are_not_pooled(self):
        local = run()
        local["runtime"] = "flue-local"
        rows = summarize([dict(run(), runtime="flue-openshell"), local])
        self.assertEqual(sorted(row["runtime"] for row in rows), ["flue-local", "flue-openshell"])

    def test_analysis_uses_only_metadata(self):
        source = run()
        source.update(prompt="PRIVATE_CANARY", source="PRIVATE_CANARY", api_key="PRIVATE_CANARY", stderr="PRIVATE_CANARY")
        value = analysis(source)
        self.assertNotIn("PRIVATE_CANARY", str(value))
        self.assertEqual(value["accounting_basis"], "cli_estimate_not_invoice")

    def test_audit_is_durable_and_rejects_arbitrary_content(self):
        with tempfile.TemporaryDirectory() as folder:
            audit = Audit(folder)
            item = {"name": "gate.closed", "sequence": 1, "aeion.context.observed": 250000}
            audit.record(run(), item)
            path = Path(folder) / ("a" * 32 + ".events.jsonl")
            self.assertIn('250000', path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(ValueError, "INVALID_AUDIT_EVENT"):
                audit.record(run(), {"prompt": "PRIVATE_CANARY"})


if __name__ == "__main__":
    unittest.main()
