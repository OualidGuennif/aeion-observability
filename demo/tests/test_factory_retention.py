"""Workspace and branch retention, owner-only agent feedback channels and crash error classes."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'app'), str(Path(__file__).resolve().parent)]
from bridge import SandboxBridge
from factory.flue_review import FlueReview
from factory.github import GitHubForge
from factory.retention import DAY_NS, Retention
from factory.store import CANCELLED, FAILED, MERGED
from local_sandbox import LocalSandbox
from runner import error_class
import test_bridge
import test_factory_target_dispatch as fixtures

NOW = 100 * DAY_NS


class RetentionTests(unittest.TestCase):
    setUp = fixtures.TargetDispatchTests.setUp

    def build(self, key, status, age_days, receipt=None, correction=None):
        if correction is None:
            build_id = self.store.admit(['013'], key, self.catalog)['build_ids'][0]
        else:
            build_id = self.store.admit(['013'], key, self.catalog, actor='supervisor',
                                        correction=correction)['build_ids'][0]
        self.set(build_id, status, age_days, receipt)
        folder = self.root / 'work' / build_id / 'repo'
        folder.mkdir(parents=True)
        (folder / 'file.txt').write_text('x')
        return build_id

    def set(self, build_id, status, age_days, receipt=None):
        conn = self.store._connect()
        with conn:
            conn.execute('UPDATE builds SET status=?, updated_ns=?, receipt=?, attempt_id=? WHERE build_id=?',
                         (status, NOW - age_days * DAY_NS, json.dumps(receipt or {}), build_id[::-1], build_id))
        conn.close()

    def test_only_old_terminal_workspaces_nobody_needs_are_removed(self):
        old = self.build('r1', FAILED, 8)
        recent = self.build('r2', CANCELLED, 2)
        needed = self.build('r3', FAILED, 9)
        merged = self.build('r5', FAILED, 30)
        self.build('r4', 'queued', 9, correction={'previous_build_id': needed, 'attempt': 2, 'round': 0})
        self.set(merged, MERGED, 30)
        stray = self.root / 'work' / 'not-a-build'
        stray.mkdir()
        unknown = self.root / 'work' / ('f' * 32)
        unknown.mkdir()
        result = Retention(self.store, self.root / 'work', clock=lambda: NOW).run()
        self.assertEqual(sorted(result['workspaces_removed']), sorted([old, merged]))
        for kept in (recent, needed):
            self.assertTrue((self.root / 'work' / kept).is_dir())
        self.assertTrue(stray.is_dir() and unknown.is_dir())

    def test_it_runs_at_start_then_once_a_day(self):
        clock = [NOW]
        retention = Retention(self.store, self.root / 'work', clock=lambda: clock[0])
        self.assertIsNotNone(retention.tick())
        clock[0] += DAY_NS - 1
        self.assertIsNone(retention.tick())
        clock[0] += 1
        self.assertIsNotNone(retention.tick())

    def test_branches_of_published_failed_builds_are_pruned_once(self):
        published = {'publisher': {'pr': {'pr_number': 7}}}
        failed = self.build('b1', FAILED, 0, receipt=published)
        self.build('b2', FAILED, 0)
        merged = self.build('b3', FAILED, 0)
        self.set(merged, MERGED, 0, published)
        attempts = {row['build_id']: row['attempt_id'] for row in self.store.board()}
        calls = []
        retention = Retention(self.store, self.root / 'work', clock=lambda: NOW,
                              prune_branch=lambda attempt: calls.append(attempt) or {'status': 'deleted'})
        self.assertEqual(retention.run()['branches_pruned'], [attempts[failed]])
        self.assertEqual(retention.run()['branches_pruned'], [])
        self.assertEqual(calls, [attempts[failed]])


class Transport:
    def __init__(self, pr, delete_status=204):
        self.pr, self.delete_status, self.calls = pr, delete_status, []

    def __call__(self, method, url, payload, headers, timeout=20):
        self.calls.append((method, url))
        if method == 'GET':
            return 200, [self.pr] if self.pr else []
        return self.delete_status, None


class PruneBranchTests(unittest.TestCase):
    attempt = 'a' * 32

    def forge(self, transport, dry_run=False):
        return GitHubForge('o/r', token='synthetic', transport=transport, dry_run=dry_run)

    def test_only_a_closed_unmerged_pull_request_releases_its_branch(self):
        closed = {'state': 'closed', 'merged_at': None}
        transport = Transport(closed)
        self.assertEqual(self.forge(transport).prune_branch(self.attempt), {'status': 'deleted'})
        self.assertEqual(transport.calls[-1],
                         ('DELETE', 'https://api.github.com/repos/o/r/git/refs/heads/aeion/build-' + 'a' * 24))
        for pr in ({'state': 'open', 'merged_at': None}, {'state': 'closed', 'merged_at': '2026-11-06'}, None):
            transport = Transport(pr)
            self.assertEqual(self.forge(transport).prune_branch(self.attempt)['status'], 'held')
            self.assertNotIn('DELETE', [method for method, _ in transport.calls])
        self.assertEqual(self.forge(Transport(closed, 422)).prune_branch(self.attempt), {'status': 'absent'})
        self.assertEqual(self.forge(Transport(closed), dry_run=True).prune_branch(self.attempt)['reason'], 'dry_run')


class FeedbackAndDiagnosticsTests(unittest.TestCase):
    def test_the_bridge_keeps_one_bounded_note(self):
        bridge = SandboxBridge(LocalSandbox())
        bridge.start()
        self.addCleanup(bridge.close)
        for body in ({'text': ''}, {'text': 'x' * 801}, {'text': 'RAS', 'path': '/x'}, {'text': 3}):
            self.assertEqual(test_bridge.post(bridge, '/v1/feedback', body)[0], 400, body)
        self.assertIsNone(bridge.feedback)
        self.assertEqual(test_bridge.post(bridge, '/v1/feedback', {'text': 'RAS'}), (200, {'ok': True}))
        self.assertEqual(bridge.feedback, 'RAS')

    def test_only_one_error_class_survives_stderr(self):
        stream = io.BytesIO(b'secret prompt text TypeError here\nuser data ECONNRESET\nmore text\n')
        self.assertEqual(error_class(stream), 'ECONNRESET')
        self.assertIsNone(error_class(io.BytesIO(b'Error: plain text only\nEXPECTED words\n')))
        self.assertEqual(error_class(io.BytesIO(b'x ERR_STREAM_PREMATURE_CLOSE y\n')), 'ERR_STREAM_PREMATURE_CLOSE')

    def test_a_reviewer_note_never_reaches_the_vote(self):
        review = FlueReview()

        class Session:
            def __init__(self, run, progress):
                self.telemetry = type('T', (), {'begin': staticmethod(lambda run: None)})()

            def live(self, run, folder, handover, prompt, kind, review_result):
                review_result.write_text(json.dumps({'verdict': 'reject', 'reason': 'scope',
                                                     'feedback': 'The packet was long.'}))
                run['native_cost_usd'] = '0'
                return 'complete'

            def finish(self, run, error):
                return {}

            def end_span(self, span, run, error):
                pass

        import factory.flue_review as module
        original = (module.FactorySession, module.usage, module.eligibility)
        module.FactorySession = Session
        module.usage = lambda run: {'complete': True, 'cost_usd': '0', 'basis': 'fixture'}
        module.eligibility = lambda model: (True, None)
        self.addCleanup(lambda: setattr(module, 'FactorySession', original[0]) or
                        setattr(module, 'usage', original[1]) or setattr(module, 'eligibility', original[2]))
        self.assertEqual(review('glm-5.3-flash', 'packet'), {'verdict': 'reject', 'reason': 'scope'})
        self.assertEqual(review.last_feedback, 'The packet was long.')


if __name__ == '__main__':
    unittest.main()
