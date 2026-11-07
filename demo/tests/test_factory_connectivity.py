"""A working CLI stop resumes the same model; a quiet stop does not. No model call."""
import json
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory.connectivity import (
    ORPHAN_MIN_AGE, Connectivity, probe_twice, reap_exited_checks, reap_idle,
    same_model_resume, session_was_working)
from factory.store import HELD, QUEUED, Store
import test_factory_target_dispatch as fixtures


class ClassifierTests(unittest.TestCase):
    def test_three_steps_or_events_mean_the_agent_was_still_working(self):
        self.assertFalse(session_was_working({'cli_steps': 2, 'forwarded_count': 2, 'finish_reason': 'toolUse'}))
        self.assertTrue(session_was_working({'cli_steps': 3}))
        self.assertTrue(session_was_working({'forwarded_count': 45}))
        self.assertTrue(session_was_working({}, tool_events=3))
        self.assertFalse(session_was_working(None, tool_events=2))

    def test_only_a_working_cli_stop_or_a_network_stop_resumes_the_same_model(self):
        working = {'cli_steps': 44, 'forwarded_count': 45, 'finish_reason': 'toolUse'}
        self.assertTrue(same_model_resume('CLI_FAILED', working))
        self.assertTrue(same_model_resume('CLI_PROTOCOL_ERROR', {}, tool_events=3))
        self.assertFalse(same_model_resume('CLI_FAILED', {'cli_steps': 2, 'forwarded_count': 2}))
        self.assertFalse(same_model_resume('CLI_STARTUP_FAILED', working))
        self.assertFalse(same_model_resume('PROVIDER_ERROR', working))
        self.assertTrue(same_model_resume('TRANSPORT_ERROR', {}))
        self.assertTrue(same_model_resume('PROVIDER_UNAVAILABLE', {'cli_steps': 0}))

    def test_both_connects_must_succeed(self):
        slept = []
        self.assertTrue(probe_twice(lambda: True, sleep=lambda seconds: slept.append(seconds)))
        self.assertEqual(slept, [1])
        answers = iter([True, False])
        self.assertFalse(probe_twice(lambda: next(answers), sleep=lambda _seconds: None))

        def down():
            raise OSError('down')

        self.assertFalse(probe_twice(down, sleep=lambda _seconds: None))

    def test_reap_removes_only_exited_check_containers(self):
        removed = []

        def docker(*args, check=True):
            class Result:
                stdout = ''
            if args[:3] == ('ps', '-a', '--filter'):
                Result.stdout = '\n'.join([
                    'aeion-check-abcdef012345',
                    'langfuse',
                    'aeion-check-pg-' + ('ab' * 8),
                    'aeion-check-short',
                    'forum',
                ])
                return Result()
            if args[:2] == ('rm', '-f'):
                removed.append(args[2])
                return Result()
            raise AssertionError(args)

        self.assertEqual(reap_exited_checks(docker),
                         ['aeion-check-abcdef012345', 'aeion-check-pg-' + ('ab' * 8)])
        self.assertEqual(removed, ['aeion-check-abcdef012345', 'aeion-check-pg-' + ('ab' * 8)])

    def test_an_idle_sweep_keeps_a_sandbox_younger_than_thirty_minutes(self):
        """Qualification has no factory lease. A young sandbox is still in use."""
        now = time.time()
        ages = {'young': 30, 'old': ORPHAN_MIN_AGE + 5}
        removed = []

        def docker(*args, check=True):
            if args[:2] == ('ps', '-a'):
                return SimpleNamespace(stdout='')
            if args[0] == 'ps':
                return SimpleNamespace(stdout='young\nold\n')
            if args[0] == 'inspect':
                created = datetime.fromtimestamp(now - ages[args[1]], timezone.utc)
                stamp = created.isoformat().replace('+00:00', 'Z')
                return SimpleNamespace(stdout=json.dumps([{'Name': '/' + args[1], 'Created': stamp}]))
            if args[:2] == ('rm', '-f'):
                removed.append(args[2])
                return SimpleNamespace(stdout='')
            raise AssertionError(args)

        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        store = Path(folder.name) / 'factory.db'
        connection = sqlite3.connect(store)
        connection.execute('CREATE TABLE builds (build_id TEXT, status TEXT, lease_until_ns INTEGER)')
        connection.commit()
        connection.close()
        self.assertEqual(Connectivity(docker=docker).reap(store), ['old'])
        report = reap_idle(store, docker=docker)
        self.assertEqual(report['removed'], ['old'])
        self.assertNotIn('young', report['containers'])
        self.assertEqual(removed, ['old', 'old'])
        self.assertGreaterEqual(ORPHAN_MIN_AGE, 1800)


class ExpiredWorkTests(unittest.TestCase):
    setUp = fixtures.TargetDispatchTests.setUp

    def expire(self, build_id):
        connection = sqlite3.connect(self.store.path)
        connection.execute('UPDATE builds SET lease_until_ns=0 WHERE build_id=?', (build_id,))
        connection.commit()
        connection.close()

    def test_tool_progress_on_an_expired_lease_queues_the_same_build(self):
        self.store.admit(['013'], 'lease-work', self.catalog)
        claimed = self.store.claim_next(self.catalog)
        for step in (1, 2, 3):
            self.assertTrue(self.store.record_progress(
                claimed['attempt_id'], claimed['attempt_generation'], 'tool.finished',
                {'model': 'deepseek-4.1-flash', 'step': step}))
        self.expire(claimed['build_id'])
        reopened = Store(self.store.path)
        row = reopened.board()[0]
        self.assertEqual(row['status'], QUEUED)
        continued = json.loads(row['receipt'])['continued']
        self.assertEqual(continued['trigger'], 'lease_expired')
        self.assertEqual(continued['model'], 'deepseek-4.1-flash')
        self.assertEqual(continued['resumes'], 1)
        self.assertIsNone(row['hold_reason'])

    def test_publication_on_an_expired_lease_stays_reconciliation_needed(self):
        self.store.admit(['013'], 'lease-publish', self.catalog)
        claimed = self.store.claim_next(self.catalog)
        for step in (1, 2, 3):
            self.store.record_progress(claimed['attempt_id'], claimed['attempt_generation'],
                                       'tool.finished', {'model': 'deepseek-4.1-flash', 'step': step})
        self.store.record_progress(claimed['attempt_id'], claimed['attempt_generation'], 'publishing', {})
        self.expire(claimed['build_id'])
        reopened = Store(self.store.path)
        row = reopened.board()[0]
        self.assertEqual(row['status'], HELD)
        self.assertEqual(row['hold_reason'], 'reconciliation_needed')


if __name__ == '__main__':
    unittest.main()
