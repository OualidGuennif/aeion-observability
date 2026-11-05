"""A valid reviewer vote is a successful reviewer response, not a routing failure."""
import sys
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.models import Router, Telemetry
from factory.review_circuit import two_vote_review


FILES = {"demo/forum/product/x.py": "print('ok')\n"}


class CircuitTelemetryTests(unittest.TestCase):
    def test_failed_vote_keeps_its_actual_typed_channel_diagnostics(self):
        execution={'engine':'flue-pi','failure':'REVIEW_RESULT_MISSING','trace_id':'a'*32,
                   'forwarded_count':1,'usage':{'complete':True,'cost_usd':'0.01'}}
        def fail(*_):raise ValueError('REVIEW_RESULT_MISSING')
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(Telemetry()),fail,
            execution_for_vote=lambda:execution)
        self.assertEqual(result['votes'][0]['execution'],execution)
        self.assertEqual(result['votes'][0]['reason'],'REVIEW_RESULT_MISSING')
    def test_baseline_diff_distinguishes_inherited_code_and_includes_untracked_additions(self):
        from factory.review_circuit import baseline_diff
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder)
            def git(*args):
                return subprocess.check_output(['git','-C',folder,*args],text=True).strip()
            git('init','-q')
            (repo/'settings.properties').write_text('database=sqlite\nlimit=1\n')
            git('add','settings.properties')
            git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','base')
            base=git('rev-parse','HEAD')
            (repo/'settings.properties').write_text('UNTRUSTED WORKTREE BASE\n')
            files={'settings.properties':'database=sqlite\nlimit=2\n','new.txt':'new\n'}
            diff=baseline_diff(repo,base,files)
            self.assertIn(' database=sqlite',diff)
            self.assertIn('-limit=1\n+limit=2',diff)
            self.assertIn('--- /dev/null\n+++ b/new.txt',diff)
            self.assertNotIn('UNTRUSTED',diff)
            seen=[]
            result=two_vote_review('glm-5.3-flash','001',files,Router(Telemetry()),
                lambda model,prompt:seen.append(prompt) or {'verdict':'reject','reason':'fixture'},
                baseline=diff,base_sha=base)
            self.assertTrue(all(diff in prompt for prompt in seen))
            self.assertEqual(result['review_input_version'],2)
            self.assertEqual(result['base_sha'],base)
            self.assertEqual(result['diff_sha256'],hashlib.sha256(diff.encode()).hexdigest())

    def test_unsafe_or_oversized_baseline_never_reaches_a_model(self):
        from factory.review_circuit import baseline_diff, CircuitError
        with tempfile.TemporaryDirectory() as folder:
            for base,files in [('invalid',{'safe.txt':'x'}),('a'*40,{'../private':'x'})]:
                with self.assertRaises(CircuitError):baseline_diff(folder,base,files)
        seen=[]
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(Telemetry()),
            lambda *args:seen.append(args),baseline='x'*240001,base_sha='a'*40)
        self.assertEqual(result['reason'],'review_input_too_large')
        self.assertEqual(seen,[])

    def test_complete_large_reviews_launch_but_utf8_byte_overflow_never_sends_an_excerpt(self):
        seen=[]
        result=two_vote_review('glm-5.3-flash','002',{'src/Migration.java':'x'*30000},Router(Telemetry()),
            lambda model,prompt:seen.append(prompt) or {'verdict':'approve','reason':'Synthetic fixture'})
        self.assertEqual(result['status'],'approved')
        self.assertEqual(len(seen),2)
        self.assertTrue(all('x'*30000 in prompt for prompt in seen))
        seen.clear()
        result=two_vote_review('glm-5.3-flash','002',{'src/Migration.java':'€'*80000},Router(Telemetry()),
            lambda model,prompt:seen.append(prompt) or {'verdict':'approve'})
        self.assertEqual(result['reason'],'review_input_too_large')
        self.assertEqual(seen,[])
    def test_review_covers_the_protected_acceptance_and_excludes_its_preparer(self):
        seen=[]
        def vote(model,prompt):
            seen.append((model,prompt))
            return {'verdict':'approve','reason':'fixture'}
        result=two_vote_review('glm-5.3-flash','007',FILES,Router(Telemetry()),vote,
            acceptance='class IndependentContract {}',preparer_model='qwen-3.8-flash')
        self.assertEqual(result['status'],'approved')
        self.assertEqual({model for model,_ in seen},{'deepseek-4.1-flash','claude-haiku-5.5'})
        self.assertTrue(all('class IndependentContract {}' in prompt for _,prompt in seen))
        self.assertEqual(result['acceptance_digest'],hashlib.sha256(b'class IndependentContract {}').hexdigest())
    def test_budget_or_local_preflight_rejection_does_not_become_a_model_failure(self):
        telemetry=Telemetry()
        def fail_before_transport(*_):raise ValueError('budget unavailable')
        result=two_vote_review('glm-5.3-flash','001',FILES,Router(telemetry),fail_before_transport,
                               observed_for_vote=lambda:False)
        self.assertEqual(result['status'],'held')
        self.assertEqual(telemetry.records,[])
    def test_reviewers_receive_and_bind_the_complete_specification(self):
        seen=[]
        spec='# Held posts\nNew submissions must stay hidden until moderation.\n'
        def vote(model,prompt):
            seen.append(prompt)
            return {'verdict':'approve','reason':'fixture'}
        result=two_vote_review('glm-5.3-flash','021',FILES,Router(Telemetry()),vote,specification=spec)
        self.assertEqual(result['status'],'approved')
        self.assertTrue(all(spec in prompt for prompt in seen))
        self.assertEqual(result['spec_digest'],hashlib.sha256(spec.encode()).hexdigest())

    def test_oversized_specification_holds_before_any_vote(self):
        def forbidden(*_):raise AssertionError('truncated review reached transport')
        result=two_vote_review('glm-5.3-flash','021',FILES,Router(Telemetry()),forbidden,
                               specification='x'*240001)
        self.assertEqual(result['reason'],'review_input_too_large')

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
