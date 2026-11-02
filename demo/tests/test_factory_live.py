"""Shared model policy, canonical wire ids and the bounded live builder (no network)."""
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.profiles import available as profile_available
from factory.dispatch import DispatchWorker
from factory.live import BuilderError, LiveBuilder, parse_files
from factory.model_client import ModelClientError, complete_with_usage
from factory.models import MODELS, Router, author_model, eligibility, eligible, wire_id


class ModelPolicyTests(unittest.TestCase):
    def test_wire_ids_are_the_documented_identifiers(self):
        self.assertEqual(wire_id("deepseek-4.1-flash"), "deepseek-v4.1-flash")
        self.assertEqual(wire_id("qwen-3.8-flash"), "qwen3.8-flash")
        self.assertEqual(wire_id("glm-5.3-flash"), "glm-5.3-flash")
        self.assertEqual(wire_id("claude-haiku-5.5"), "claude-haiku-5-5")

    def test_the_author_choice_is_shared_and_deterministic(self):
        self.assertEqual(author_model(), "glm-5.3-flash")
        self.assertEqual(author_model(exclude_models=("glm-5.3-flash",)), "qwen-3.8-flash")
        self.assertEqual(Router().select("review", exclude_families=("anthropic",)),
                         "glm-5.3-flash")

    def test_the_four_owner_authorized_workers_are_present(self):
        self.assertEqual(set(MODELS), {"glm-5.3-flash", "qwen-3.8-flash",
                                       "deepseek-4.1-flash", "claude-haiku-5.5"})

    def test_an_unknown_model_has_no_wire_id(self):
        with self.assertRaises(ValueError):
            wire_id("made-up-model")

    def test_the_app_and_the_factory_read_one_eligibility_verdict(self):
        # The app's DeepSeek profile expired on 2026-10-31; the owner's spend authorization on
        # 2026-11-02 does not requalify it, so both mechanisms must say no.
        self.assertEqual(eligibility("deepseek-4.1-flash"), (False, "profile_expired"))
        self.assertFalse(profile_available("deepseek"))
        self.assertTrue(profile_available("glm"))
        self.assertEqual(profile_available("glm"), eligibility("glm-5.3-flash")[0])
        self.assertNotIn("deepseek-4.1-flash", eligible())
        self.assertNotEqual(Router().select("review"), "deepseek-4.1-flash")

    def test_an_ineligible_model_is_refused_before_transport(self):
        calls = []

        def transport(url, payload, headers):
            calls.append(payload)
            return 200, {"choices": [{"message": {"content": '{"verdict":"approve"}'}}]}

        with self.assertRaises(ModelClientError) as caught:
            complete_with_usage("deepseek-4.1-flash", "prompt", transport=transport)
        self.assertIn("model_ineligible:profile_expired", str(caught.exception))
        self.assertEqual(calls, [])


class ModelClientTests(unittest.TestCase):
    def setUp(self):
        self.transport_calls = []

    def transport(self, status=200, body=None):
        def call(url, payload, headers):
            self.transport_calls.append({"url": url, "payload": payload, "headers": headers})
            return status, body if body is not None else {
                "choices": [{"message": {"content": '{"verdict":"approve"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "cost": 0.002},
            }
        return call

    def test_the_wire_id_is_sent_and_usage_is_returned(self):
        with mock.patch.dict("os.environ", {"OPENCODE_API_KEY": "fixture"}, clear=False), \
                mock.patch("factory.model_client.load_environment", return_value=[]):
            result = complete_with_usage("glm-5.3-flash", "prompt", transport=self.transport())
        call = self.transport_calls[0]
        self.assertEqual(call["payload"]["model"], "glm-5.3-flash")
        self.assertEqual(call["headers"]["User-Agent"], "aeion-factory/1.0")
        self.assertTrue(call["headers"]["x-opencode-session"])
        self.assertEqual(result["answer"], {"verdict": "approve"})
        self.assertEqual(result["usage"]["cost_usd"], 0.002)
        self.assertTrue(result["usage"]["complete"])

    def test_an_unreported_cost_is_incomplete_not_free(self):
        body = {"choices": [{"message": {"content": '{"verdict":"reject"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4}}
        with mock.patch.dict("os.environ", {"OPENCODE_API_KEY": "fixture"}, clear=False), \
                mock.patch("factory.model_client.load_environment", return_value=[]):
            result = complete_with_usage("glm-5.3-flash", "prompt", transport=self.transport(body=body))
        self.assertIsNone(result["usage"]["cost_usd"])
        self.assertFalse(result["usage"]["complete"])
        self.assertEqual(result["usage"]["basis"], "provider_cost_unreported")


class LiveBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.brief = self.repo / "BRIEF.md"
        self.brief.write_text("# Feature 013 Security headers\n")
        self.frozen = SimpleNamespace(write_scopes=[
            "src/main/java/local/aeion/forum/", "src/test/java/local/aeion/forum/"])
        self.feature = {"id": "013", "title": "Security headers and CSP"}

    def client(self, files, cost=0.01):
        def call(model, prompt, max_tokens=0):
            return {"answer": {"files": files}, "wire_model": wire_id(model),
                    "usage": {"cost_usd": cost, "complete": cost is not None,
                              "input_tokens": 100, "output_tokens": 50}}
        return call

    def test_files_are_written_inside_the_scopes_and_usage_is_kept(self):
        builder = LiveBuilder(client=self.client([
            {"path": "src/main/java/local/aeion/forum/Filter.java", "content": "class Filter {}\n"}]))
        written = builder(repo=self.repo, frozen=self.frozen, feature=self.feature,
                          brief=self.brief)
        self.assertEqual(written, ["src/main/java/local/aeion/forum/Filter.java"])
        self.assertTrue((self.repo / written[0]).is_file())
        self.assertEqual(builder.last_usage["cost_usd"], 0.01)

    def test_a_path_outside_the_scopes_is_refused_before_writing(self):
        builder = LiveBuilder(client=self.client([
            {"path": "build.gradle", "content": "malicious"}]))
        with self.assertRaises(BuilderError):
            builder(repo=self.repo, frozen=self.frozen, feature=self.feature, brief=self.brief)
        self.assertFalse((self.repo / "build.gradle").exists())

    def test_malformed_and_escaping_answers_are_refused(self):
        for files in ([{"path": "../outside.java", "content": "x"}],
                      [{"path": "/etc/passwd", "content": "x"}],
                      [{"path": "src/main/java/local/aeion/forum/A.java", "content": "x"},
                       {"path": "src/main/java/local/aeion/forum/A.java", "content": "y"}]):
            with self.assertRaises(BuilderError):
                parse_files({"files": files}, self.frozen.write_scopes, repo=self.repo)

    def test_a_sibling_prefix_is_not_inside_a_scope_without_a_trailing_slash(self):
        with self.assertRaises(BuilderError):
            parse_files({"files": [{"path": "src/main/java/local/aeion/forumX/A.java",
                                    "content": "x"}]},
                        ["src/main/java/local/aeion/forum"], repo=self.repo)

    def test_relative_steps_never_escape_a_scope_by_textual_prefix(self):
        # Six `..` steps from the scope reach the repository root, then `.git` is unreviewed:
        # `git diff` and `git ls-files` do not show it.
        for path in ("src/main/java/local/aeion/forum/../../../../../../.git/hooks/pre-push",
                     "src/main/java/local/aeion/forum/./A.java",
                     "src/main/java/local/aeion/forum/.git/hooks/pre-push",
                     "src/main/java/local/aeion/forum/.GIT/config"):
            with self.assertRaises(BuilderError):
                parse_files({"files": [{"path": path, "content": "x"}]},
                            self.frozen.write_scopes, repo=self.repo)
        self.assertFalse((self.repo / ".git").exists())

    def test_a_failed_second_call_does_not_reuse_the_previous_usage(self):
        state = {"fail": False}

        def call(model, prompt, max_tokens=0):
            if state["fail"]:
                raise RuntimeError("transport unavailable")
            return {"answer": {"files": [{
                "path": "src/main/java/local/aeion/forum/Filter.java",
                "content": "class Filter {}\n"}]},
                "usage": {"cost_usd": 0.01, "complete": True}}

        builder = LiveBuilder(client=call)
        builder(repo=self.repo, frozen=self.frozen, feature=self.feature, brief=self.brief)
        self.assertEqual(builder.last_usage["cost_usd"], 0.01)
        state["fail"] = True
        with self.assertRaises(RuntimeError):
            builder(repo=self.repo, frozen=self.frozen, feature=self.feature, brief=self.brief)
        self.assertIsNone(builder.last_usage)

    def test_a_symlinked_write_target_is_refused(self):
        outside_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_tmp.cleanup)
        outside = Path(outside_tmp.name)
        (self.repo / "src/main/java/local/aeion/forum").mkdir(parents=True)
        (self.repo / "src/main/java/local/aeion/forum/link").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(BuilderError):
            parse_files({"files": [{"path": "src/main/java/local/aeion/forum/link/A.java",
                                    "content": "x"}]},
                        self.frozen.write_scopes, repo=self.repo)

    def test_an_empty_answer_is_refused(self):
        with self.assertRaises(BuilderError):
            parse_files({"files": []}, self.frozen.write_scopes, repo=self.repo)
        with self.assertRaises(BuilderError):
            parse_files({"no": "files"}, self.frozen.write_scopes, repo=self.repo)


class WorkerSettlementTests(unittest.TestCase):
    def test_a_review_circuit_means_zero_transport_is_not_proven(self):
        worker = DispatchWorker.__new__(DispatchWorker)
        worker.paid = False
        worker.review_complete = lambda model, prompt: {"verdict": "approve"}
        self.assertFalse(worker._zero_transport_proven())
        worker.review_complete = None
        self.assertTrue(worker._zero_transport_proven())
        worker.paid = True
        self.assertFalse(worker._zero_transport_proven())

    def setUp(self):
        self.worker = DispatchWorker.__new__(DispatchWorker)
        self.worker.budget = mock.Mock()
        self.worker.last_usage = None
        self.reservation = SimpleNamespace(id="reservation-fixture")

    def test_measured_cost_is_settled(self):
        self.worker.last_usage = {"cost_usd": 0.03, "complete": True}
        self.worker._settle(self.reservation)
        self.worker.budget.settle.assert_called_once_with(self.reservation, Decimal("0.03"))

    def test_unknown_or_incomplete_usage_is_not_settled(self):
        for usage in (None, {"complete": False}, {"complete": True, "cost_usd": None}):
            self.worker.last_usage = usage
            self.worker._settle(self.reservation)
        self.worker.budget.settle.assert_not_called()


if __name__ == "__main__":
    unittest.main()
