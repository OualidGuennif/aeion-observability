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
from factory.budget import DailyBudget
from factory.agent_files import BuilderError, parse_files
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


    def test_the_six_owner_authorized_workers_are_present(self):
        self.assertEqual(set(MODELS), {"glm-5.3-flash", "qwen-3.8-flash", "deepseek-4.1-flash",
                                       "claude-haiku-5.5", "gpt-6-luna", "minimax-m3.1-flash"})


    def test_an_unknown_model_has_no_wire_id(self):
        with self.assertRaises(ValueError):
            wire_id("made-up-model")




class ExportedFilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.brief = self.repo / "BRIEF.md"
        self.brief.write_text("# Feature 013 Security headers\n")
        self.frozen = SimpleNamespace(write_scopes=[
            "src/main/java/local/aeion/forum/", "src/test/java/local/aeion/forum/"])
        self.feature = {"id": "013", "title": "Security headers and CSP"}


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


    def test_an_intermediate_symlink_cannot_redirect_a_write_outside_the_scope(self):
        scope = self.repo / "src/main/java/local/aeion/forum"
        outside = self.repo / ".git/hooks"
        scope.mkdir(parents=True)
        outside.mkdir(parents=True)
        (scope / "redirect").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(BuilderError):
            parse_files({"files": [{"path": "src/main/java/local/aeion/forum/redirect/pre-push",
                                    "content": "x"}]},
                        self.frozen.write_scopes, repo=self.repo)
        self.assertFalse((outside / "pre-push").exists())


    def test_an_empty_answer_is_refused(self):
        with self.assertRaises(BuilderError):
            parse_files({"files": []}, self.frozen.write_scopes, repo=self.repo)
        with self.assertRaises(BuilderError):
            parse_files({"no": "files"}, self.frozen.write_scopes, repo=self.repo)

    def test_grader_tampering_files_are_refused_by_parse_files(self):
        scopes = ["src/main/java/local/aeion/forum/", "src/test/java/local/aeion/forum/", "src/main/resources/"]
        for entry in (
            {"path": "src/test/java/local/aeion/forum/Skip.java",
             "content": "package local.aeion.forum;\nimport org.junit.jupiter.api.extension.InvocationInterceptor;\n"},
            {"path": "src/main/resources/META-INF/services/org.junit.jupiter.api.extension.Extension",
             "content": "local.aeion.forum.Skip\n"},
            {"path": "src/main/resources/junit-platform.properties",
             "content": "junit.jupiter.extensions.autodetection.enabled=true\n"},
            {"path": "src/test/java/local/aeion/forum/Shadow.java",
             "content": "package org.junit.jupiter.api;\npublic class Assertions {}\n"},
        ):
            with self.assertRaisesRegex(BuilderError, "builder_grader_tampered"):
                parse_files({"files": [entry]}, scopes, repo=self.repo)




class ReviewBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.budget = DailyBudget(
            Path(self.tmp.name) / "ledger.jsonl",
            limits={"aeion-observability": Decimal("15.00"),
                    "aeion-autonomous-forum": Decimal("15.00")},
            today=lambda: "2026-11-02")
        self.worker = DispatchWorker.__new__(DispatchWorker)
        self.worker.budget = self.budget
        self.worker.budget_scope = "aeion-autonomous-forum"


    def entries(self):
        path = Path(self.tmp.name) / "ledger.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


    def test_each_vote_reserves_and_settles_its_own_usage(self):
        class Review:
            last_usage = None

            def __call__(inner, model, prompt):
                inner.last_usage = {"cost_usd": 0.02, "complete": True}
                return {"verdict": "approve"}

        self.worker.review_complete = Review()
        self.assertEqual(self.worker._review_vote("glm-5.3-flash", "prompt"),
                         {"verdict": "approve"})
        self.assertEqual([entry["kind"] for entry in self.entries()], ["reserve", "settle"])
        self.assertEqual(self.budget.spent("aeion-autonomous-forum"), Decimal("0.02"))


    def test_a_raising_callback_cannot_settle_the_previous_votes_usage(self):
        class Review:
            last_usage = None

            def __init__(inner):
                inner.calls = 0

            def __call__(inner, model, prompt):
                inner.calls += 1
                if inner.calls == 1:
                    inner.last_usage = {"cost_usd": 0.02, "complete": True}
                    return {"verdict": "approve"}
                raise RuntimeError("provider down")

        self.worker.review_complete = Review()
        self.worker._review_vote("glm-5.3-flash", "prompt")
        with self.assertRaises(RuntimeError):
            self.worker._review_vote("qwen-3.8-flash", "prompt")
        self.assertEqual([entry["kind"] for entry in self.entries()],
                         ["reserve", "settle", "reserve"])
        self.assertEqual(self.budget.spent("aeion-autonomous-forum"), Decimal("0.07"))


    def test_an_unknown_vote_keeps_its_reservation_open(self):
        class Review:
            last_usage = None

            def __call__(inner, model, prompt):
                inner.last_usage = {"complete": False}
                return {"verdict": "approve"}

        self.worker.review_complete = Review()
        with self.assertRaisesRegex(ValueError,'USAGE_UNKNOWN'):
            self.worker._review_vote("qwen-3.8-flash", "prompt")
        self.assertEqual([entry["kind"] for entry in self.entries()], ["reserve"])
        self.assertEqual(self.budget.spent("aeion-autonomous-forum"), Decimal("0.05"))

    def test_review_reservation_matches_the_supervisor_role_limit(self):
        budget=self.budget
        class Review:
            cost_limit='1.00'
            paid=True
            last_usage=None
            def __call__(inner,model,prompt):
                self.assertEqual(budget.spent('aeion-autonomous-forum'),Decimal('1.00'))
                inner.last_usage={'complete':True,'cost_usd':'0.02'}
                return {'verdict':'approve'}
        self.worker.review_complete=Review()
        self.worker._review_vote('qwen-3.8-flash','complete review fixture')
        self.assertEqual(self.budget.spent('aeion-autonomous-forum'),Decimal('0.02'))




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



if __name__ == "__main__": unittest.main()
