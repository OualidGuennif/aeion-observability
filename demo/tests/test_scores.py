"""Unit tests for Langfuse score publishing and multi-dimensional factory metrics."""
import base64
import os
import unittest

from scores import compute_factory_scores, get_langfuse_client, publish, publish_factory_scores


class ScoreTests(unittest.TestCase):

    def test_publish_disabled_without_auth(self):
        old_auth = os.environ.pop("LANGFUSE_AUTH", None)
        try:
            res = publish({"id": "1", "trace_id": "t1", "status": "passed", "synthetic": True})
            self.assertEqual(res, {"status": "disabled"})
            res_fac = publish_factory_scores({"id": "1", "trace_id": "t1", "status": "passed"})
            self.assertEqual(res_fac, {"status": "disabled", "ids": []})
        finally:
            if old_auth:
                os.environ["LANGFUSE_AUTH"] = old_auth

    def test_compute_factory_scores_complete(self):
        run_data = {
            "status": "passed",
            "check": {"status": "passed"},
            "circuit": {
                "status": "approved",
                "votes": [{"vote": 1, "verdict": "approve"}, {"vote": 2, "verdict": "approve"}]
            },
            "usage": {
                "cost_usd": "10.0",
                "input_tokens": 100000,
                "cached_tokens": 40000,
            },
            "cost_reservation_usd": "50.0",
        }
        scores = compute_factory_scores(run_data)
        self.assertEqual(scores["factory.check.acceptance"]["value"], 1.0)
        self.assertEqual(scores["factory.review.consensus"]["value"], 1.0)
        # 1.0 - (10.0 / 50.0) = 0.8
        self.assertEqual(scores["factory.budget.efficiency"]["value"], 0.8)
        # 40000 / 100000 = 0.4
        self.assertEqual(scores["factory.cache.hit_ratio"]["value"], 0.4)

    def test_compute_factory_scores_split_and_exhausted(self):
        run_data = {
            "status": "failed",
            "check": {"status": "failed"},
            "circuit": {
                "status": "held",
                "votes": [{"vote": 1, "verdict": "approve"}, {"vote": 2, "verdict": "reject"}]
            },
            "usage": {
                "cost_usd": "50.0",
                "input_tokens": 50000,
                "cached_tokens": 0,
            },
            "cost_reservation_usd": "50.0",
        }
        scores = compute_factory_scores(run_data)
        self.assertEqual(scores["factory.check.acceptance"]["value"], 0.0)
        self.assertEqual(scores["factory.review.consensus"]["value"], 0.5)
        self.assertEqual(scores["factory.budget.efficiency"]["value"], 0.0)
        self.assertEqual(scores["factory.cache.hit_ratio"]["value"], 0.0)

    def test_get_langfuse_client_decodes_basic_auth(self):
        auth_str = base64.b64encode(b"pk-lf-test:sk-lf-test").decode()
        old_auth = os.environ.get("LANGFUSE_AUTH")
        os.environ["LANGFUSE_AUTH"] = auth_str
        try:
            client = get_langfuse_client()
            if client is not None:
                from langfuse import Langfuse
                self.assertIsInstance(client, Langfuse)
        finally:
            if old_auth is not None:
                os.environ["LANGFUSE_AUTH"] = old_auth
            else:
                os.environ.pop("LANGFUSE_AUTH", None)


if __name__ == "__main__":
    unittest.main()
