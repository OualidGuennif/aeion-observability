"""Bounded automatic correction rounds after a reviewer rejection or a failed gate; no model call."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory.agent_files import BuilderError
from factory.dispatch import DispatchWorker, correction_feedback, next_step
from factory.flue_builder import FlueBuilder, attempt_text, correction_text
from factory.models import RoutingError
from factory.publish import FakeForge
from factory.store import (FAILED, HELD, MAX_ATTEMPTS, MAX_CORRECTION_ROUNDS, QUEUED, SIMULATED_COMPLETE,
                           StoreError, continuation_link)
import test_factory_target_dispatch as fixtures

SOURCE = "demo/forum-app/src/main/java/local/aeion/forum/Feature.java"


class Author:
    """Writes one scoped file; a correction keeps or changes it and records what it received.

    ``crash`` maps a call number (1-based) to the exception that call raises after writing.
    """

    def __init__(self, unchanged=False, crash=None, models=None, feedback=None, execution=None):
        self.calls, self.unchanged, self.crash = [], unchanged, crash or {}
        self.models, self.feedback, self.execution = models, feedback, execution
        self.last_execution = self.last_feedback = None
        if models:
            self.model = models[0]

    def run_build(self, *, repo, build, correction=None, **_):
        self.calls.append(correction)
        number = len(self.calls)
        if self.models:
            # The paid path records the author model; a stand-in proves the supervisor's choice.
            self.model = self.models[number - 1]
        version = number if not (self.unchanged and correction) else 1
        if correction and correction.get('files'):
            self.started_from = dict(correction['files'])
        path = repo / SOURCE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"package local.aeion.forum;\n// version {version}\n")
        self.last_feedback = self.feedback
        self.last_execution = {'build_id': build['build_id'], 'failure': None, 'error_class': 'TypeError'}
        if self.execution:
            self.last_execution.update(self.execution)
        if number in self.crash:
            raise self.crash[number]


class Reviews:
    def __init__(self, rejections):
        self.rejections, self.calls = rejections, 0

    def __call__(self, model, prompt):
        self.calls += 1
        if self.rejections > 0:
            self.rejections -= 1
            return {"verdict": "reject", "reason": "moves the default port 8081→8080; not requested"}
        return {"verdict": "approve", "reason": "in scope"}


class CorrectionRoundTests(unittest.TestCase):
    setUp = fixtures.TargetDispatchTests.setUp

    def worker(self, author, reviews, command=None):
        target = self.target
        if command is not None:
            import dataclasses
            target = dataclasses.replace(target, protected_check=dataclasses.replace(
                target.protected_check, command=command))
        return DispatchWorker(self.store, self.catalog, self.specs, self.root / "work", fixtures.config(),
            target=target, builder=author, forge=FakeForge(), review_complete=reviews,
            require_circuit=True, author_model="deepseek-4.1-flash", allow_unbudgeted=True)

    def builds(self):
        return self.store.board()

    def test_a_rejection_becomes_the_next_rounds_input_and_the_correction_ships(self):
        self.store.admit(["013"], "c1", self.catalog)
        author, reviews = Author(), Reviews(rejections=1)
        self.worker(author, reviews).run_once()
        first, second = self.builds()
        self.assertEqual(first["status"], FAILED)
        marker = json.loads(first["receipt"])["correction"]
        self.assertEqual((marker["round"], marker["trigger"]), (0, "reviewer_rejected"))
        self.assertEqual(marker["candidate_files"], [SOURCE])
        self.assertEqual(second["status"], QUEUED)
        self.assertEqual(self.store.correction_of(second["build_id"]),
                         {"previous_build_id": first["build_id"], "attempt": 1, "round": 1})

        self.worker(author, reviews).run_once()
        correction = author.calls[1]
        self.assertEqual(correction["round"], 1)
        self.assertIn("A reviewer rejected it: moves the default port 8081→8080; not requested",
                      correction["feedback"])
        self.assertEqual(author.started_from, {SOURCE: "package local.aeion.forum;\n// version 1\n"})
        self.assertEqual(self.builds()[1]["status"], SIMULATED_COMPLETE)
        self.assertIsNone(author.calls[0])

    def test_rounds_then_attempts_are_bounded_then_the_owner_decides(self):
        self.store.admit(["013"], "c2", self.catalog)
        author, reviews = Author(), Reviews(rejections=99)
        sessions = MAX_ATTEMPTS * (MAX_CORRECTION_ROUNDS + 1)
        for _ in range(sessions + 2):
            self.worker(author, reviews).run_once()
        statuses = [build["status"] for build in self.builds()]
        self.assertEqual(statuses, [FAILED] * (sessions - 1) + [HELD])
        last = self.builds()[-1]
        self.assertEqual(last["hold_reason"], "owner_review_required")
        self.assertEqual(json.loads(last["receipt"])["correction"],
                         {"attempt": MAX_ATTEMPTS, "round": MAX_CORRECTION_ROUNDS, "exhausted": True})
        self.assertEqual(len(author.calls), sessions)
        positions = [(c["attempt"], c["round"]) for c in author.calls[1:]]
        self.assertEqual(positions, [(1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2)])
        # A new attempt still learns why the last candidate was refused and starts from it.
        self.assertTrue(author.calls[3]["feedback"])
        self.assertIsNotNone(author.calls[3]["files"])

    def test_a_crash_starts_the_next_attempt_from_the_validated_candidate(self):
        self.store.admit(["013"], "c7", self.catalog)
        author = Author(crash={1: ValueError("CLI_FAILED")})
        reviews = Reviews(rejections=0)
        self.worker(author, reviews).run_once()
        first, second = self.builds()
        marker = json.loads(first["receipt"])["correction"]
        self.assertEqual((marker["attempt"], marker["round"], marker["trigger"]), (1, 0, "crash"))
        self.assertEqual(marker["crash"], {"failure": "CLI_FAILED", "error_class": "TypeError"})
        self.assertEqual(marker["candidate_files"], [SOURCE])
        self.assertEqual(self.store.correction_of(second["build_id"]),
                         {"previous_build_id": first["build_id"], "attempt": 2, "round": 0})
        self.assertEqual(reviews.calls, 0)
        self.worker(author, reviews).run_once()
        correction = author.calls[1]
        self.assertEqual((correction["attempt"], correction["round"], correction["trigger"]), (2, 0, "crash"))
        self.assertEqual(correction["crash"], {"failure": "CLI_FAILED", "error_class": "TypeError"})
        self.assertEqual(author.started_from, {SOURCE: "package local.aeion.forum;\n// version 1\n"})
        self.assertIn("NEW ATTEMPT AFTER A CRASH", correction_text(correction))
        self.assertEqual(self.builds()[1]["status"], SIMULATED_COMPLETE)

    def test_a_cli_failure_while_the_agent_was_still_working_resumes_the_same_model(self):
        self.store.admit(["013"], "c14", self.catalog)
        author = Author(crash={1: ValueError("CLI_FAILED")}, execution={
            'cli_steps': 44, 'forwarded_count': 45, 'finish_reason': 'toolUse',
            'error_class': 'IllegalStateException'})
        ghosts = type('Ghosts', (), {'paths': [], 'reap': lambda self, path: self.paths.append(path)})()
        worker = self.worker(author, Reviews(rejections=0))
        worker.connectivity = ghosts
        worker.run_once()
        self.assertEqual(len(self.builds()), 1)
        resumed = self.builds()[0]
        self.assertEqual(resumed['status'], QUEUED)
        continued = json.loads(resumed['receipt'])['continued']
        self.assertEqual(continued['trigger'], 'cli_interrupted')
        self.assertEqual(continued['failure'], 'CLI_FAILED')
        self.assertEqual(continued['error_class'], 'IllegalStateException')
        self.assertEqual(continued['cli_steps'], 44)
        self.assertEqual(continued['resumes'], 1)
        self.assertEqual(continued['model'], 'deepseek-4.1-flash')
        self.assertEqual(ghosts.paths, [self.store.path])
        self.assertNotIn('correction', json.loads(resumed['receipt']))

        self.worker(author, Reviews(rejections=0)).run_once()
        correction = author.calls[1]
        self.assertTrue(correction['resume'])
        self.assertEqual((correction['attempt'], correction['round'], correction['trigger']),
                         (1, 0, 'cli_interrupted'))
        self.assertEqual(correction['model'], 'deepseek-4.1-flash')
        self.assertEqual(author.started_from, {SOURCE: "package local.aeion.forum;\n// version 1\n"})
        text = correction_text(correction)
        self.assertIn('CONTINUE THE SAME ATTEMPT', text)
        self.assertIn('IllegalStateException', text)
        self.assertIn('44 tool steps', text)
        self.assertNotIn('NEW ATTEMPT AFTER A CRASH', text)
        self.assertEqual(len(self.builds()), 1)
        self.assertEqual(self.builds()[0]['status'], SIMULATED_COMPLETE)

    def test_a_cli_failure_before_real_work_still_starts_another_model(self):
        self.store.admit(["013"], "c15", self.catalog)
        author = Author(crash={1: ValueError("CLI_FAILED")}, execution={
            'cli_steps': 2, 'forwarded_count': 2, 'finish_reason': 'toolUse',
            'error_class': 'IllegalStateException'})
        self.worker(author, Reviews(rejections=0)).run_once()
        first, second = self.builds()
        self.assertEqual(json.loads(first['receipt'])['correction']['trigger'], 'crash')
        self.assertEqual(self.store.correction_of(second['build_id'])['attempt'], 2)

    def test_a_startup_failure_stays_a_crash_even_after_tool_steps(self):
        self.store.admit(["013"], "c16", self.catalog)
        author = Author(crash={1: ValueError("CLI_STARTUP_FAILED")}, execution={
            'cli_steps': 44, 'forwarded_count': 45, 'error_class': 'IllegalStateException'})
        self.worker(author, Reviews(rejections=0)).run_once()
        self.assertEqual(json.loads(self.builds()[0]['receipt'])['correction']['trigger'], 'crash')
        self.assertEqual(self.store.correction_of(self.builds()[1]['build_id']),
                         {'previous_build_id': self.builds()[0]['build_id'], 'attempt': 2, 'round': 0})

    def test_a_provider_error_stays_a_crash_even_when_the_agent_had_been_working(self):
        self.store.admit(["013"], "c17", self.catalog)
        author = Author(crash={1: ValueError("PROVIDER_ERROR")}, execution={
            'cli_steps': 44, 'forwarded_count': 45, 'error_class': 'IllegalStateException'})
        self.worker(author, Reviews(rejections=0)).run_once()
        self.assertEqual(json.loads(self.builds()[0]['receipt'])['correction']['trigger'], 'crash')
        self.assertEqual(self.store.correction_of(self.builds()[1]['build_id'])['attempt'], 2)

    def test_a_network_stop_resumes_the_same_model_without_saved_steps(self):
        self.store.admit(["013"], "c18", self.catalog)
        author = Author(crash={1: ValueError("TRANSPORT_ERROR")})
        self.worker(author, Reviews(rejections=0)).run_once()
        self.assertEqual(len(self.builds()), 1)
        self.assertEqual(json.loads(self.builds()[0]['receipt'])['continued']['trigger'], 'network')
        self.worker(author, Reviews(rejections=0)).run_once()
        self.assertEqual(author.calls[1]['trigger'], 'network')
        self.assertTrue(author.calls[1]['resume'])
        self.assertEqual(author.calls[1]['model'], 'deepseek-4.1-flash')
        self.assertEqual(self.builds()[0]['status'], SIMULATED_COMPLETE)

    def test_three_same_model_resumes_then_a_fourth_stop_is_a_crash(self):
        self.store.admit(["013"], "c19", self.catalog)
        author = Author(crash={n: ValueError("CLI_FAILED") for n in range(1, 5)}, execution={
            'cli_steps': 44, 'forwarded_count': 45, 'error_class': 'IllegalStateException'})
        reviews = Reviews(rejections=0)
        for _ in range(3):
            self.worker(author, reviews).run_once()
        self.assertEqual(len(self.builds()), 1)
        self.assertEqual(self.builds()[0]['status'], QUEUED)
        self.assertEqual(json.loads(self.builds()[0]['receipt'])['continued']['resumes'], 3)
        self.worker(author, reviews).run_once()
        self.assertEqual(self.builds()[0]['status'], FAILED)
        self.assertEqual(json.loads(self.builds()[0]['receipt'])['correction']['trigger'], 'crash')
        self.assertEqual(self.store.correction_of(self.builds()[1]['build_id'])['attempt'], 2)

    def test_a_down_provider_holds_the_build_and_does_not_start_the_author(self):
        self.store.admit(["013"], "c20", self.catalog)
        author = Author()
        author.paid = True
        author.last_usage = {'complete': True, 'cost_usd': '0', 'basis': 'fixture'}

        class Link:
            def __init__(self):
                self.up = False
                self.calls = 0
            def reachable(self):
                self.calls += 1
                return self.up
            def reap(self, _path):
                return []

        link = Link()
        worker = self.worker(author, Reviews(rejections=0))
        worker.connectivity = link
        worker.run_once()
        self.assertEqual(author.calls, [])
        self.assertEqual(self.builds()[0]['status'], HELD)
        self.assertEqual(self.builds()[0]['hold_reason'], 'network_unavailable')
        self.assertGreaterEqual(link.calls, 1)
        link.up = True
        worker.run_once()
        self.assertEqual(len(author.calls), 1)
        self.assertNotEqual(self.builds()[0]['hold_reason'], 'network_unavailable')

    def test_a_stale_sandbox_proof_holds_the_same_build_and_starts_no_author(self):
        self.store.admit(["013"], "c21", self.catalog)
        author = Author()
        author.paid = True
        author.last_usage = {'complete': True, 'cost_usd': '0', 'basis': 'fixture'}
        worker = self.worker(author, Reviews(rejections=0))
        worker.security_fresh = lambda: False
        worker.run_once()
        self.assertEqual(author.calls, [])
        self.assertEqual(len(self.builds()), 1)
        self.assertEqual(self.builds()[0]['status'], HELD)
        self.assertEqual(self.builds()[0]['hold_reason'], 'sandbox_qualification_stale')
        worker.security_fresh = lambda: True
        worker.run_once()
        self.assertEqual(len(self.builds()), 1)
        self.assertEqual(len(author.calls), 1)
        self.assertNotIn('correction', json.loads(self.builds()[0]['receipt'] or '{}'))
        self.assertNotEqual(self.builds()[0]['hold_reason'], 'sandbox_qualification_stale')

    def test_an_unchanged_candidate_after_a_crash_is_still_judged(self):
        self.store.admit(["013"], "c8", self.catalog)
        author, reviews = Author(unchanged=True, crash={1: ValueError("AGENT_TIMEOUT")}), Reviews(rejections=0)
        self.worker(author, reviews).run_once()
        self.worker(author, reviews).run_once()
        self.assertEqual(self.builds()[1]["status"], SIMULATED_COMPLETE)

    def test_boundary_stops_never_continue(self):
        for number, error in enumerate((BuilderError("protected_harness_changed"), ValueError("USAGE_UNKNOWN"),
                                        ValueError("ATTEMPT_REVOKED"), RuntimeError("boom"))):
            with self.subTest(error=error):
                self.store.admit(["013"], "c9-" + str(number), self.catalog)
                self.worker(Author(crash={1: error}), Reviews(rejections=0)).run_once()
                last = self.builds()[-1]
                self.assertEqual(last["status"], FAILED)
                self.assertNotIn("correction", json.loads(last["receipt"]))

    def test_a_crash_in_the_last_attempt_waits_for_the_owner(self):
        self.store.admit(["013"], "c10", self.catalog)
        author = Author(crash={n: ValueError("PROVIDER_ERROR") for n in range(1, 10)})
        for _ in range(MAX_ATTEMPTS + 1):
            self.worker(author, Reviews(rejections=0)).run_once()
        self.assertEqual(len(author.calls), MAX_ATTEMPTS)
        self.assertEqual([b["status"] for b in self.builds()], [FAILED] * MAX_ATTEMPTS)
        self.assertTrue(json.loads(self.builds()[-1]["receipt"])["correction"]["exhausted"])

    def test_a_new_attempt_excludes_every_model_of_the_launch_and_a_round_keeps_its_model(self):
        self.store.admit(["013"], "c11", self.catalog)
        author = Author(models=["glm-5.3-flash"] * 3 + ["qwen-3.8-flash"])
        author.paid = True
        author.last_usage = {"complete": True, "cost_usd": "0", "basis": "fixture"}
        reviews = Reviews(rejections=99)
        for _ in range(4):
            self.worker(author, reviews).run_once()
        self.assertEqual(author.calls[1]["model"], "glm-5.3-flash")
        self.assertEqual(author.calls[1]["exclude_models"], [])
        self.assertIsNone(author.calls[3]["model"])
        self.assertEqual(author.calls[3]["exclude_models"], ["glm-5.3-flash"])

    def test_a_secret_in_owner_feedback_is_redacted_before_the_next_author(self):
        self.store.admit(["013"], "c12", self.catalog)
        author, reviews = Author(feedback="The brief is unclear about ports. ghp_" + "a" * 36), Reviews(rejections=1)
        self.worker(author, reviews).run_once()
        receipt = json.loads(self.builds()[0]["receipt"])
        self.assertEqual(receipt["feedback"], {"author": "[redacted]"})
        self.worker(author, reviews).run_once()
        sent = json.dumps(author.calls[1])
        self.assertNotIn("ports", sent)
        self.assertNotIn("ghp_", sent)

    def test_a_clean_author_note_reaches_the_next_author_as_untrusted_data(self):
        self.store.admit(["013"], "c13", self.catalog)
        author, reviews = Author(feedback="The brief is unclear about ports."), Reviews(rejections=1)
        self.worker(author, reviews).run_once()
        self.worker(author, reviews).run_once()
        self.assertIn("Untrusted author note: The brief is unclear about ports.", author.calls[1]["feedback"])

    def test_an_unchanged_correction_is_held_without_checks_or_reviews(self):
        self.store.admit(["013"], "c3", self.catalog)
        author, reviews = Author(unchanged=True), Reviews(rejections=1)
        self.worker(author, reviews).run_once()
        calls = reviews.calls
        self.worker(author, reviews).run_once()
        second = self.builds()[1]
        self.assertEqual((second["status"], second["hold_reason"]), (HELD, "owner_review_required"))
        self.assertEqual(json.loads(second["receipt"])["reason"], "correction_unchanged")
        self.assertEqual(reviews.calls, calls)
        self.assertEqual(len(self.builds()), 2)

    def test_a_failed_gate_is_corrected_with_the_check_result(self):
        self.store.admit(["013"], "c4", self.catalog)
        author, reviews = Author(), Reviews(rejections=0)
        self.worker(author, reviews, command=[sys.executable, "-c", "raise SystemExit(1)", "{repo}"]).run_once()
        first, second = self.builds()
        self.assertEqual(json.loads(first["receipt"])["correction"]["trigger"], "gate_failed")
        self.assertEqual(reviews.calls, 0)
        self.worker(author, reviews).run_once()
        self.assertTrue(any(line.startswith("Protected check gradle_test failed: ")
                            for line in author.calls[1]["feedback"]))
        self.assertEqual(self.builds()[1]["status"], SIMULATED_COMPLETE)

    def test_a_changed_candidate_is_not_reused_but_its_feedback_is(self):
        self.store.admit(["013"], "c5", self.catalog)
        author, reviews = Author(), Reviews(rejections=1)
        self.worker(author, reviews).run_once()
        first = self.builds()[0]
        (self.root / "work" / first["build_id"] / "repo" / SOURCE).write_text("tampered\n")
        self.worker(author, reviews).run_once()
        self.assertIsNone(author.calls[1]["files"])
        self.assertIsNone(author.calls[1]["candidate_digest"])
        self.assertTrue(author.calls[1]["feedback"])

    def test_only_a_failed_attempt_of_the_same_feature_can_be_corrected(self):
        self.store.admit(["013"], "c6", self.catalog)
        queued = self.builds()[0]["build_id"]
        for number, correction in enumerate((
                {"previous_build_id": queued, "round": 1},
                {"previous_build_id": queued, "round": MAX_CORRECTION_ROUNDS + 1},
                {"previous_build_id": queued, "attempt": MAX_ATTEMPTS + 1, "round": 0},
                {"previous_build_id": queued, "attempt": 1, "round": 0},
                {"previous_build_id": queued, "attempt": True, "round": 1},
                {"previous_build_id": "x" * 32, "round": 1})):
            with self.subTest(correction=correction), self.assertRaisesRegex(StoreError, "correction_invalid"):
                self.store.admit(["013"], "c6-" + str(number), self.catalog,
                                 actor="supervisor", correction=correction)

    def test_links_and_steps(self):
        build = "a" * 32
        self.assertEqual(continuation_link({"previous_build_id": build, "round": 2}),
                         {"previous_build_id": build, "attempt": 1, "round": 2})
        self.assertIsNone(continuation_link({"previous_build_id": build, "attempt": 2, "round": 0, "x": 1}))
        self.assertEqual(next_step(1, 0), (1, 1))
        self.assertEqual(next_step(1, MAX_CORRECTION_ROUNDS), (2, 0))
        self.assertEqual(next_step(1, 0, crash=True), (2, 0))
        self.assertIsNone(next_step(MAX_ATTEMPTS, MAX_CORRECTION_ROUNDS))
        self.assertIsNone(next_step(MAX_ATTEMPTS, 0, crash=True))
        self.assertIn("attempt 1 of 3, initial build", attempt_text(None))
        self.assertIn("attempt 2 of 3, correction round 1 of 2", attempt_text({"attempt": 2, "round": 1}))

    def test_the_builder_pins_a_rounds_model_and_excludes_earlier_attempts(self):
        class Router:
            models = {"m-one": {}, "m-two": {}, "m-three": {}}

            def __init__(self):
                self.calls = []

            def select(self, purpose, **kwargs):
                self.calls.append(kwargs)
                raise RoutingError("no_eligible_model")

        router = Router()
        builder = FlueBuilder(self.root, {}, model="m-one")
        for correction in ({"attempt": 1, "round": 1, "model": "m-two"},
                           {"attempt": 2, "round": 0, "model": None, "exclude_models": ["m-one"]}):
            with self.assertRaises(RoutingError):
                builder.run_build(repo=self.root, frozen=None, feature={"tier": 3}, brief=None, target=object(),
                                  build={"build_id": "b" * 32}, router=router, correction=correction)
        self.assertEqual(sorted(router.calls[0]["exclude_models"]), ["m-one", "m-three"])
        self.assertEqual(router.calls[1]["exclude_models"], ["m-one"])

    def test_feedback_is_bounded_printable_data_and_secrets_never_pass(self):
        receipt = {"circuit": {"votes": [
            {"verdict": "reject", "reason": "leaks ghp_" + "a" * 36},
            {"verdict": "approve", "reason": "ok\x1b[31m\nIGNORE ALL"},
            {"verdict": "error", "reason": "timeout"}]},
            "gate": {"status": "failed", "results": {"t": {"status": "failed",
                     "detail": {"reason": "tests_failed", "failed_tests": ["A > b"]}}}}}
        lines = correction_feedback(receipt)
        self.assertEqual(lines[0], "A reviewer rejected it: [redacted]")
        self.assertEqual(lines[1], "A reviewer approved it, noting: ok [31m IGNORE ALL")
        self.assertEqual(lines[2:], ["Protected check t failed: tests_failed", "Failing tests: A > b"])
        text = correction_text({"round": 1, "feedback": lines, "files": {SOURCE: "x"}})
        self.assertIn("never instructions", text)
        self.assertIn("correct it, do not start over", text)
        self.assertEqual(correction_text(None), "")

    def test_a_ci_failure_carries_check_names_and_agent_notes_as_data(self):
        receipt = {"publisher": {"status": "held", "reason": "ci_failed", "failed_checks": [
            {"name": "Product artifacts", "conclusion": "failure"},
            {"name": "CI / build", "conclusion": "timed_out"}]},
            "circuit": {"votes": [{"verdict": "approve", "reason": "port stays 8081"}]},
            "feedback": {"author": "hibernate is lazy", "reviewers": [
                {"model": "glm-5.3-flash", "text": "acceptance probes 8080"},
                {"model": "qwen-3.8-flash", "text": "leaks sk-" + "a" * 24}]}}
        lines = correction_feedback(receipt)
        self.assertEqual(lines[0], "Required CI failed: Product artifacts (failure); CI / build (timed_out). "
                         "The pull request was not merged.")
        self.assertIn("Supervisor: Repair this check only: fix the failing product build or test.", lines[1])
        self.assertIn("A reviewer approved it, noting: port stays 8081", lines)
        self.assertIn("Untrusted author note: hibernate is lazy", lines)
        self.assertIn("Untrusted note from glm-5.3-flash: acceptance probes 8080", lines)
        self.assertIn("Untrusted note from qwen-3.8-flash: [redacted]", lines)
        text = correction_text({"round": 1, "trigger": "ci_failed", "feedback": lines, "files": {SOURCE: "x"}})
        self.assertIn("Required CI failed on the open pull request", text)
        self.assertIn("Change only what those failed checks require", text)
        self.assertIn("was not merged", text)
        self.assertNotIn("was refused", text)


if __name__ == "__main__":
    unittest.main()
