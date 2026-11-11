"""Unit tests for the Factory Model Arbiter and Re-ranker."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.arbiter import EmpiricalScorer, ModelArbiter
from factory.models import Router, Telemetry


class ArbiterTests(unittest.TestCase):
    def setUp(self):
        self.arbiter = ModelArbiter()
        self.candidates = ["glm-5.3-flash", "qwen-3.8-flash", "deepseek-4.1-flash"]

    def test_cold_start_empirical_scores_follow_order_prior(self):
        stats = {m: {"n": 0} for m in self.candidates}
        selected, meta = self.arbiter.arbitrate(self.candidates, "author", stats)
        self.assertEqual(selected, "glm-5.3-flash")
        self.assertEqual(meta["basis"], "empirical_multi_factor")
        self.assertGreater(meta["scores"]["glm-5.3-flash"], meta["scores"]["deepseek-4.1-flash"])

    def test_latency_penalty_demotes_slow_models(self):
        stats = {
            "glm-5.3-flash": {"n": 5, "success_rate": 1.0, "avg_cost_usd": "0.02", "avg_latency_ms": 250000},  # slow
            "qwen-3.8-flash": {"n": 5, "success_rate": 1.0, "avg_cost_usd": "0.02", "avg_latency_ms": 5000},   # fast
        }
        score_slow = EmpiricalScorer.calculate_score("glm-5.3-flash", stats["glm-5.3-flash"])
        score_fast = EmpiricalScorer.calculate_score("qwen-3.8-flash", stats["qwen-3.8-flash"])
        self.assertGreater(score_fast, score_slow)

    def test_agent_reranking_selects_and_annotates_complexity(self):
        def fake_agent(prompt, timeout=5):
            return '{"complexity": "HIGH", "ranking": ["deepseek-4.1-flash", "glm-5.3-flash"], "selected": "deepseek-4.1-flash", "rationale": "Complex boundary requires max reasoning."}'

        arbiter = ModelArbiter(agent_role=fake_agent)
        stats = {m: {"n": 5, "success_rate": 1.0} for m in self.candidates}
        selected, meta = arbiter.arbitrate(self.candidates, "author", stats, task_context={"title": "Complex Arch", "synthetic": False})
        self.assertEqual(selected, "deepseek-4.1-flash")
        self.assertEqual(meta["basis"], "intelligent_agent_reranked")
        self.assertEqual(meta["complexity"], "HIGH")
        self.assertIn("reasoning", meta["rationale"])

    def test_agent_failure_fails_closed_to_empirical(self):
        def crashing_agent(prompt, timeout=5):
            raise TimeoutError("Model timeout")

        arbiter = ModelArbiter(agent_role=crashing_agent)
        stats = {m: {"n": 5, "success_rate": 1.0} for m in self.candidates}
        selected, meta = arbiter.arbitrate(self.candidates, "author", stats, task_context={"title": "Task", "synthetic": False})
        self.assertEqual(meta["basis"], "empirical_multi_factor")
        self.assertIn(selected, self.candidates)

    def test_router_delegates_to_arbiter_when_context_provided(self):
        telemetry = Telemetry()
        router = Router(telemetry=telemetry)
        selected = router.select("author", task_context={"title": "Task 1"})
        self.assertIn(selected, router.models)
        self.assertIn("empirical", router.last_decision["basis"])


if __name__ == "__main__":
    unittest.main()
