"""A valid reviewer vote is a successful reviewer response, not a routing failure."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.models import Router, Telemetry
from factory.review_circuit import two_vote_review


FILES = {"demo/forum/product/x.py": "print('ok')\n"}


class CircuitTelemetryTests(unittest.TestCase):
    def test_two_approvals_are_recorded_as_successes(self):
        telemetry = Telemetry()
        result = two_vote_review("deepseek-4.1-flash", "001", FILES,
                                 Router(telemetry), lambda model, prompt: {"verdict": "approve", "reason": "ok"})
        self.assertEqual(result["status"], "approved")
        self.assertEqual(len(result["votes"]), 2)
        for vote in result["votes"]:
            stats = telemetry.stats(vote["model"], "review")
            self.assertEqual(stats["n"], 1)
            self.assertEqual(stats["success_rate"], 1.0)

    def test_a_valid_rejection_is_also_a_successful_response(self):
        telemetry = Telemetry()
        result = two_vote_review("deepseek-4.1-flash", "001", FILES,
                                 Router(telemetry), lambda model, prompt: {"verdict": "reject", "reason": "no"})
        self.assertEqual(result["status"], "held")
        self.assertEqual(len(result["votes"]), 1)
        stats = telemetry.stats(result["votes"][0]["model"], "review")
        self.assertEqual(stats["n"], 1)
        self.assertEqual(stats["success_rate"], 1.0)

    def test_a_malformed_answer_is_still_a_failure(self):
        telemetry = Telemetry()
        result = two_vote_review("deepseek-4.1-flash", "001", FILES,
                                 Router(telemetry), lambda model, prompt: {"verdict": "maybe"})
        self.assertEqual(result["status"], "held")
        stats = telemetry.stats(result["votes"][0]["model"], "review")
        self.assertEqual(stats["n"], 1)
        self.assertEqual(stats["success_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
