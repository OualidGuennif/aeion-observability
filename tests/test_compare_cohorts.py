"""Protect the example's denominator and unknown-quality semantics."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cohorts", ROOT / "examples/compare_cohorts.py")
cohorts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cohorts)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/cohort-comparison.json").read_text())

    def test_bundled_example_includes_failed_and_assisted_costs(self):
        cheap, balanced = cohorts.summarize(self.data)
        self.assertEqual((cheap["cohort_cost_usd"], cheap["verified_autonomous_successes"]), ("72.00", 6))
        self.assertEqual(cheap["cost_per_autonomous_success_usd"], "12.00")
        self.assertEqual((balanced["cohort_cost_usd"], balanced["verified_autonomous_successes"]), ("82.00", 9))
        self.assertEqual(balanced["p95_wall_seconds_nearest_rank"], 600)

    def test_zero_successes_is_undefined(self):
        for task in self.data["policies"][0]["tasks"]:
            task["outcome"] = "failed"
        self.assertIsNone(cohorts.summarize(self.data)[0]["cost_per_autonomous_success_usd"])

    def test_missing_intervention_coverage_is_unknown(self):
        self.data["policies"][0]["tasks"][0]["intervention_coverage"] = "incomplete"
        row = cohorts.summarize(self.data)[0]
        self.assertIsNone(row["verified_autonomous_successes"])
        self.assertIsNone(row["cost_per_autonomous_success_usd"])
        self.assertEqual(row["quality_evidence"], "unknown")

    def test_unmatured_outcome_is_unknown(self):
        self.data["policies"][0]["tasks"][0]["maturity"] = "pending"
        self.assertEqual(cohorts.summarize(self.data)[0]["quality_evidence"], "unknown")

    def test_invalid_or_missing_cost_is_rejected(self):
        for value in ["NaN", "Infinity", "-0.01", "not-a-number", 4]:
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data["policies"][0]["tasks"][0]["costs"]["inference"] = value
                with self.assertRaises(ValueError):
                    cohorts.summarize(data)
        del self.data["policies"][0]["tasks"][0]["costs"]["sandbox"]
        with self.assertRaises(ValueError):
            cohorts.summarize(self.data)

    def test_duplicate_task_is_rejected(self):
        self.data["policies"][0]["tasks"].append(self.data["policies"][0]["tasks"][0])
        with self.assertRaises(ValueError):
            cohorts.summarize(self.data)

    def test_corrective_work_cannot_be_an_autonomous_success(self):
        self.data["policies"][0]["tasks"][0]["corrective_minutes"] = 1
        with self.assertRaises(ValueError):
            cohorts.summarize(self.data)

    def test_non_synthetic_input_is_not_accepted(self):
        self.data["example_only"] = False
        with self.assertRaises(ValueError):
            cohorts.summarize(self.data)


if __name__ == "__main__":
    unittest.main()
