"""One configured worker resolves distinct feature targets and holds errors without spending."""
import dataclasses
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.api import FactoryApp,ApiError
from factory.budget import DailyBudget
from factory.dispatch import DispatchWorker
from factory.execution import resolve
from factory.target import load_target
from test_factory_execution import feature, write_profile


class FeatureTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_profile(self.root)
        path = self.root / 'demo/forum/targets/forum-app-013.json'
        profile = json.loads(path.read_text())
        (self.root / 'brief-017.md').write_text('# Feature 017 — strict request validation\n')
        profile.update(id='fixture-017', feature_id='017', brief='brief-017.md')
        other = path.with_name('forum-app-017.json')
        other.write_text(json.dumps(profile))
        self.targets = {'013': load_target(path, self.root), '017': load_target(other, self.root)}
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(dict(schema_version=2, count=2,
                                           features=[feature('013'), feature('017')])))
        self.calls = []
        def builder(repo, frozen, feature, brief):
            self.calls.append((feature['id'], brief.read_text()))
            target = repo / frozen.write_scopes[0] / ('Feature' + feature['id'] + '.java')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('// ' + feature['id'] + '\n')
        self.app = FactoryApp(manifest, self.root / 'state', spec_dir=self.root,
                              bootstrap_token='fixture-only',
                              budget=DailyBudget(self.root / 'ledger.jsonl'),
                              execution={'mode': 'live', 'targets': self.targets, 'builder': builder})

    def test_each_feature_uses_its_own_brief_and_check_through_the_same_app(self):
        self.app.store.admit(['013', '017'], 'two-features', self.app.catalog)
        for _ in range(2): self.app.tick()
        self.assertEqual([fid for fid, _ in self.calls], ['013', '017'])
        self.assertIn('Security headers', self.calls[0][1])
        self.assertIn('strict request validation', self.calls[1][1])
        rows = self.app.store.board()
        self.assertEqual({row['status'] for row in rows}, {'simulated_complete'})
        for row in rows:
            receipt = json.loads(row['receipt'])
            self.assertEqual(receipt['feature_id'], row['feature_id'])
            self.assertEqual(receipt['gate']['results']['gradle_test']['status'], 'passed')

    def test_catalog_marks_both_valid_targets_ready(self):
        view = self.app.catalog_view(None)[1]
        self.assertEqual(view['execution']['target_features'], ['013', '017'])
        self.assertTrue(all(f['availability']['selectable'] for f in view['features']))

    def test_expired_admission_pauses_an_unstarted_queue_and_recovers_without_restart(self):
        fresh=[True];self.app.execution['admission_check']=lambda:fresh[0]
        self.app.store.admit(['017'],'fresh-before-queue',self.app.catalog)
        fresh[0]=False
        view=self.app.catalog_view(None)[1]
        self.assertEqual(view['execution']['hold_reason'],'flue_factory_unqualified')
        self.assertFalse(any(f['availability']['selectable'] for f in view['features']))
        self.assertIsNone(self.app.tick())
        self.assertEqual(self.app.store.board()[0]['status'],'queued')
        self.assertEqual(self.calls,[])
        fresh[0]=True
        self.app.tick()
        self.assertEqual(self.app.store.board()[0]['status'],'simulated_complete')

    def test_expired_admission_refuses_new_queue_and_revokes_active_model_authority(self):
        fresh=[True];self.app.execution['admission_check']=lambda:fresh[0]
        self.app.store.admit(['017'],'active-before-expiry',self.app.catalog)
        build=self.app.store.claim_next(self.app.catalog)
        self.assertTrue(self.app.worker._attempt_authorized(build))
        fresh[0]=False
        self.assertFalse(self.app.worker._attempt_authorized(build))
        session=self.app.auth.login('fixture-only')
        with self.assertRaises(ApiError) as raised:
            self.app.queue('127.0.0.1:8088','http://127.0.0.1:8088',session,session['csrf'],
                {'ids':['013'],'idempotency_key':'refuse-expired'})
        self.assertEqual(raised.exception.code,'flue_factory_unqualified')

    def test_live_resolver_prepares_each_md_without_a_manual_target_profile(self):
        with mock.patch('factory.execution.provider_available', return_value=True), \
                mock.patch('factory.execution.flue_factory_ready', return_value=False):
            execution = resolve(self.root, 'live')
        self.assertIsNotNone(execution['preparer'])
        self.assertNotIn('targets',execution)
        self.assertEqual(execution['hold_reason'],'flue_factory_unqualified')

    def test_missing_target_holds_before_budget_reservation(self):
        self.app.worker.targets.pop('017')
        self.app.store.admit(['017'], 'missing-target', self.app.catalog)
        result = self.app.tick()
        self.assertEqual(result['result']['reason'], 'target_unavailable')
        self.assertFalse((self.root / 'ledger.jsonl').exists())
        self.assertEqual(self.calls, [])

    def test_an_unexpected_check_error_is_a_visible_hold_and_does_not_freeze_the_queue(self):
        self.app.store.admit(['013', '017'], 'error-then-next', self.app.catalog)
        with mock.patch('factory.dispatch.target_check', return_value=mock.Mock(side_effect=RuntimeError('fixture-only'))):
            result = self.app.tick()
        self.assertEqual(result['result']['reason'], 'worker_error')
        self.assertEqual(self.app.store.board()[0]['status'], 'held')
        self.app.tick()
        self.assertEqual(self.app.store.board()[1]['status'], 'simulated_complete')

    def test_a_paid_builder_requires_the_independent_review_circuit_by_default(self):
        self.app.worker.builder.paid = True
        worker = DispatchWorker(self.app.store, self.app.catalog, self.root, self.root / 'work',
                                builder=self.app.worker.builder)
        self.assertTrue(worker.require_circuit)

    def test_the_claim_covers_the_target_check_and_three_bounded_model_calls(self):
        self.app.worker.builder.timeout_seconds=900
        def review(model,prompt):return {'verdict':'approve','reason':'Synthetic lease fixture'}
        review.timeout_seconds=180
        self.app.worker.review_complete=review
        self.app.worker.require_circuit=True
        self.app.store.admit(['017'], 'long-check', self.app.catalog)
        with mock.patch.object(self.app.store, 'claim_next', wraps=self.app.store.claim_next) as claim:
            self.app.tick()
        check_seconds = max(t.protected_check.timeout_seconds for t in self.targets.values())
        self.assertGreaterEqual(claim.call_args.kwargs.get('lease_ns', 0),
                                (check_seconds + 900 + 2 * 180 + 60) * 1_000_000_000)


if __name__ == '__main__':
    unittest.main()
