import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.models import MODELS, Router, RoutingError, Telemetry, eligible, family
from factory.review_circuit import MAX_PROMPT_CHARS, two_vote_review

FILES = {"demo/forum/product/x.js": "export function f() { return 1; }\n"}


def approving(model, prompt):
    return {"verdict": "approve", "reason": "looks fine"}


def rejecting(model, prompt):
    return {"verdict": "reject", "reason": "exfiltrates token"}


def broken(model, prompt):
    raise RuntimeError("provider down")


class RegistryTests(unittest.TestCase):
    def test_six_models_in_six_families(self):
        self.assertEqual(len(MODELS), 6)
        self.assertEqual(len({spec["family"] for spec in MODELS.values()}), 6)

    def test_eligible_excludes_models_and_families(self):
        remaining = eligible(exclude_models=["glm-5.3-flash"])
        self.assertNotIn("glm-5.3-flash", remaining)
        self.assertEqual(len(remaining), 5)
        self.assertEqual(eligible(exclude_families=["anthropic", "openai", "mistral"]),
                         ["deepseek-4.1-flash", "glm-5.3-flash", "qwen-3.8-flash"])

    def test_router_prefers_efficiency_then_is_deterministic(self):
        router = Router()
        first = router.select("review")
        self.assertEqual(first, router.select("review"))
        self.assertEqual(family(first), "zhipu")  # Explicit cold-start preference, not quality evidence.

    def test_telemetry_moves_the_choice_away_from_a_failing_model(self):
        telemetry = Telemetry()
        for _ in range(5):
            telemetry.record("glm-5.3-flash", "review", "error", latency_ms=900)
        self.assertNotEqual(Router(telemetry).select("review"), "glm-5.3-flash")

    def test_no_eligible_model_raises(self):
        with self.assertRaisesRegex(RoutingError, "no_eligible_model"):
            Router().select("review", exclude_families=["zhipu", "qwen", "deepseek", "anthropic",
                                                        "openai", "mistral"])

    def test_new_models_follow_the_measured_ones_in_the_cold_start_order(self):
        self.assertEqual(Router().select("author", require_role="author"), "glm-5.3-flash")
        self.assertEqual(Router().select("review", exclude_families=["zhipu", "qwen", "deepseek", "anthropic"]),
                         "gpt-6-luna")


class CircuitTests(unittest.TestCase):
    def setUp(self):
        self.telemetry = Telemetry()
        self.router = Router(self.telemetry)

    def test_two_distinct_families_never_the_author(self):
        result = two_vote_review("claude-haiku-5.5", "001", FILES, self.router, approving)
        self.assertEqual(result["status"], "approved")
        models = [v["model"] for v in result["votes"]]
        self.assertEqual(len(set(models)), 2)
        self.assertNotIn("claude-haiku-5.5", models)
        families = {family(m) for m in models}
        self.assertNotIn("anthropic", families)
        self.assertEqual(len(families), 2)

    def test_author_is_excluded_even_when_it_is_the_cheapest(self):
        result = two_vote_review("glm-5.3-flash", "001", FILES, self.router, approving)
        self.assertNotIn("glm-5.3-flash", [v["model"] for v in result["votes"]])

    def test_first_rejection_holds_without_asking_the_second_model(self):
        calls = []

        def reject_once(model, prompt):
            calls.append(model)
            return rejecting(model, prompt)

        result = two_vote_review("deepseek-4.1-flash", "001", FILES, self.router, reject_once)
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "reviewer_rejected")
        self.assertEqual(len(calls), 1)

    def test_a_failing_reviewer_holds_and_never_approves(self):
        result = two_vote_review("qwen-3.8-flash", "001", FILES, self.router, broken)
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "reviewer_failed")
        self.assertEqual(result["votes"][0]["verdict"], "error")

    def test_approval_requires_both_votes(self):
        answers = iter([{"verdict": "approve", "reason": "ok"}, {"verdict": "reject", "reason": "no"}])
        result = two_vote_review("glm-5.3-flash", "001", FILES, self.router, lambda m, p: next(answers))
        self.assertEqual(result["status"], "held")
        self.assertEqual([v["verdict"] for v in result["votes"]], ["approve", "reject"])

    def test_malformed_answer_is_a_hold(self):
        result = two_vote_review("glm-5.3-flash", "001", FILES, self.router, lambda m, p: "lgtm")
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "reviewer_failed")

    def test_empty_diff_is_held_without_calling_any_model(self):
        calls = []
        result = two_vote_review("glm-5.3-flash", "001", {}, self.router,
                                 lambda m, p: calls.append(m) or {"verdict": "approve"})
        self.assertEqual(result["status"], "held")
        self.assertEqual(calls, [])

    def test_telemetry_records_both_votes(self):
        two_vote_review("claude-haiku-5.5", "001", FILES, self.router, approving)
        self.assertEqual(len(self.telemetry.records), 2)
        self.assertEqual({r["purpose"] for r in self.telemetry.records}, {"review"})

    def test_digest_is_stable_for_the_same_outcome(self):
        a = two_vote_review("claude-haiku-5.5", "001", FILES, Router(Telemetry()), approving)
        b = two_vote_review("claude-haiku-5.5", "001", FILES, Router(Telemetry()), approving)
        self.assertEqual(a["digest"], b["digest"])

    def test_oversized_single_file_is_held_without_calling_a_model(self):
        big = {"demo/forum/product/x.js": "a" * (MAX_PROMPT_CHARS + 1)}
        calls = []

        def capture(model, prompt):
            calls.append(model)
            return {"verdict": "approve", "reason": "ok"}

        result = two_vote_review("glm-5.3-flash", "001", big, self.router, capture)
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "review_input_too_large")
        self.assertEqual(calls, [])
        self.assertFalse(result["coverage"]["complete"])
        self.assertGreater(result["coverage"]["chars"], result["coverage"]["limit_chars"])

    def test_a_tail_file_never_disappears_from_the_review_envelope(self):
        files = {
            "demo/forum/product/a.txt": "a" * (MAX_PROMPT_CHARS + 1),
            "demo/forum/product/z.txt": "TAIL_COVERAGE_FIXTURE",
        }
        seen = []

        def capture(model, prompt):
            seen.append(prompt)
            return {"verdict": "approve", "reason": "ok"}

        result = two_vote_review("glm-5.3-flash", "001", files, self.router, capture)
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "review_input_too_large")
        self.assertEqual(seen, [])
        self.assertEqual(result["coverage"]["files"], sorted(files))

    def test_a_small_java_feature_and_its_tests_receive_two_complete_reviews(self):
        files = {'src/Validation.java': 'a' * 5000, 'test/ValidationTest.java': 'b' * 4000}
        seen = []
        def capture(model, prompt):
            seen.append(prompt)
            return approving(model, prompt)
        result = two_vote_review('glm-5.3-flash', '017', files, self.router, capture)
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(len(seen), 2)
        self.assertTrue(all(files[path] in prompt for prompt in seen for path in files))
        self.assertTrue(result['coverage']['complete'])

    def test_an_unknown_author_cannot_start_a_review(self):
        calls = []
        result = two_vote_review("mystery-model", "001", FILES, self.router,
                                 lambda model, prompt: calls.append(model) or {"verdict": "approve"})
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "author_identity_unknown")
        self.assertEqual(calls, [])

    def test_an_approved_circuit_records_complete_coverage(self):
        result = two_vote_review("claude-haiku-5.5", "001", FILES, self.router, approving)
        self.assertEqual(result["status"], "approved")
        self.assertTrue(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["files"], sorted(FILES))
        self.assertEqual(len(result["content_digest"]), 64)

    def test_a_timeout_holds_the_circuit(self):
        def timing_out(model, prompt):
            raise TimeoutError("provider timeout")

        result = two_vote_review("glm-5.3-flash", "001", FILES, self.router, timing_out)
        self.assertEqual(result["status"], "held")
        self.assertEqual(result["reason"], "reviewer_failed")


if __name__ == "__main__":
    unittest.main()
