"""The canary monitor: pinned policy, fail-closed verdicts, deterministic verdicts."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import canary


def sample(**overrides):
    base = {"requests": 1000, "errors_5xx": 0, "error_rate": 0.002,
            "p95_ms": 120.0, "cache_hit_rate": 0.72}
    base.update(overrides)
    return base


class PolicyTests(unittest.TestCase):
    def test_no_samples_is_not_yet_evidence(self):
        verdict = canary.evaluate([])
        self.assertEqual(verdict["verdict"], "insufficient")
        self.assertEqual(verdict["reason"], "no_traffic")

    def test_idle_samples_are_ignored_rather_than_judged(self):
        verdict = canary.evaluate([sample(requests=0), sample(requests=0)])
        self.assertEqual(verdict["verdict"], "insufficient")
        self.assertEqual(verdict["reason"], "no_traffic")

    def test_too_few_samples_cannot_advance(self):
        verdict = canary.evaluate([sample(), sample()])
        self.assertEqual(verdict["verdict"], "insufficient")
        self.assertIn("insufficient_samples:2/4", verdict["reason"])

    def test_healthy_samples_continue(self):
        verdict = canary.evaluate([sample() for _ in range(4)])
        self.assertEqual(verdict["verdict"], "continue")
        self.assertEqual(verdict["violations"], [])
        self.assertEqual(verdict["first_violation"], None)

    def test_a_single_5xx_rolls_back(self):
        verdict = canary.evaluate([sample(), sample(errors_5xx=1, error_rate=0.001), sample(), sample()])
        self.assertEqual(verdict["verdict"], "rollback")
        self.assertEqual(verdict["first_violation"]["code"], "five_xx")

    def test_latency_and_cache_hold_instead_of_rolling_back(self):
        slow = canary.evaluate([sample(p95_ms=900.0) for _ in range(4)])
        self.assertEqual(slow["verdict"], "hold")
        self.assertEqual(slow["reason"], "policy_violation:p95_ms")
        cold = canary.evaluate([sample(cache_hit_rate=0.10) for _ in range(4)])
        self.assertEqual(cold["verdict"], "hold")
        self.assertEqual(cold["reason"], "policy_violation:cache_hit_rate")

    def test_error_rate_breach_rolls_back(self):
        verdict = canary.evaluate([sample(error_rate=0.05) for _ in range(4)])
        self.assertEqual(verdict["verdict"], "rollback")

    def test_a_request_burst_is_surfaced(self):
        verdict = canary.evaluate([sample(requests=500_000) for _ in range(4)])
        self.assertEqual(verdict["verdict"], "hold")
        self.assertIn("request_burst", {v["code"] for v in verdict["violations"]})

    def test_the_same_series_always_gives_the_same_verdict(self):
        series = [sample(), sample(p95_ms=500.0), sample(), sample()]
        first = canary.evaluate(series)
        for _ in range(5):
            self.assertEqual(canary.evaluate(series), first)

    def test_an_untrusted_sample_is_refused(self):
        with self.assertRaisesRegex(canary.CanaryError, "sample_missing:p95_ms"):
            canary.evaluate([{"requests": 1, "errors_5xx": 0, "error_rate": 0.0, "cache_hit_rate": 0.5}])
        with self.assertRaisesRegex(canary.CanaryError, "sample_invalid:error_rate"):
            canary.evaluate([sample(error_rate=1.7)])
        with self.assertRaisesRegex(canary.CanaryError, "sample_invalid:errors_5xx"):
            canary.evaluate([sample(errors_5xx=-1)])


class StatsTests(unittest.TestCase):
    def test_stats_become_a_sample(self):
        built = canary.sample_from_stats({"requests": 200, "status_5xx": 2, "cache_hits": 30,
                                          "cache_misses": 70, "p95_ms": 90})
        self.assertEqual(built["error_rate"], 0.01)
        self.assertEqual(built["cache_hit_rate"], 0.30)
        canary.validate_sample(built)

    def test_zero_traffic_does_not_divide_by_zero(self):
        built = canary.sample_from_stats({"requests": 0, "status_5xx": 0, "cache_hits": 0,
                                          "cache_misses": 0, "p95_ms": 0})
        self.assertEqual(built["error_rate"], 0.0)
        self.assertEqual(built["cache_hit_rate"], 0.0)

    def test_the_series_is_bounded_and_ordered(self):
        series = []
        for index in range(60):
            series = canary.record(series, sample(requests=index))
        self.assertEqual(len(series), 48)
        self.assertEqual(series[0]["requests"], 12)
        self.assertEqual(series[-1]["requests"], 59)

    def test_summary_is_json_safe(self):
        summary = canary.summarise([sample(), sample(error_rate=0.004)])
        self.assertEqual(summary["samples"], 2)
        self.assertEqual(summary["worst_error_rate"], 0.004)
        self.assertIn("policy", summary)


if __name__ == "__main__":
    unittest.main()
