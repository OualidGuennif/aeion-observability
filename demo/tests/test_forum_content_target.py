"""007 is a real configured next target, using isolated operator state and no transport."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.api import ApiError, FactoryApp
from factory.budget import DailyBudget
from factory.execution import resolve
from factory.target import load_target

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'demo/forum/targets/forum-app-007.json'


class ContentTargetTests(unittest.TestCase):
    def setUp(self):
        data = json.loads(PROFILE.read_text())
        if not (ROOT / data['base']['source']).is_dir():
            self.skipTest('canonical product checkout is local-only')
        self.target = load_target(PROFILE, ROOT)

    def test_the_new_feature_has_its_own_external_contract_and_pinned_source(self):
        self.assertEqual(self.target.feature_id, '007')
        self.assertEqual(self.target.target_repo, 'OualidGuennif/aeion-autonomous-forum')
        self.assertEqual(self.target.protected_check.contract_test.name, 'ContentSanitizationContractTest.java')
        self.assertIn('ThreadService.java', self.target.source_context())
        self.assertIn('ThreadsResource.java', self.target.source_context())
        self.assertTrue(self.target.brief.read_text().startswith('# 007'))

    def test_the_real_catalog_allows_operator_admission_and_preserves_existing_locks(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch(
                'factory.execution.provider_available', return_value=True), mock.patch(
                'factory.execution.flue_factory_ready', return_value=True):
            execution = resolve(ROOT, 'live')
            self.assertIsNotNone(execution['preparer'])
            self.assertEqual(execution['target_errors'], {})
            app = FactoryApp(ROOT / 'demo/forum/features/MANIFEST.json', Path(directory) / 'state',
                             bootstrap_token='synthetic-operator-only',
                             budget=DailyBudget(Path(directory) / 'ledger.jsonl'), execution=execution)
            for fid in ('001', '013', '017'):
                app.store.seed_merged(fid, app.catalog)
            session = app.auth.login('synthetic-operator-only')
            features = {f['id']: f for f in app.catalog_view(session)[1]['features']}
            self.assertTrue(features['007']['availability']['selectable'])
            self.assertEqual(features['007']['availability']['state'], 'ready')
            self.assertFalse(features['017']['availability']['selectable'])
            self.assertFalse(features['008']['availability']['selectable'])
            status, result, _ = app.queue('127.0.0.1:8088', 'http://127.0.0.1:8088', session,
                                         session['csrf'], {'ids': ['007'], 'idempotency_key': 'first'})
            self.assertEqual(status, 200)
            self.assertEqual(result['status'], 'admitted')
            with self.assertRaises(ApiError) as repeated:
                app.queue('127.0.0.1:8088', 'http://127.0.0.1:8088', session, session['csrf'],
                          {'ids': ['007'], 'idempotency_key': 'second'})
            self.assertEqual(repeated.exception.status, 409)
            self.assertFalse((Path(directory) / 'ledger.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
