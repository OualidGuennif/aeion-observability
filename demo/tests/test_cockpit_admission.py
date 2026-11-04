"""Persistent feature locks and truthful operator availability. No model or service calls."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.api import ApiError, FactoryApp
from factory.manifest import Catalog
from factory.store import Store, StoreError, LIVE_COMPLETE, SIMULATED_COMPLETE


def feature(fid, dependencies=()):
    return dict(id=fid, title=f'Feature {fid}', area='foundation', size='S', parallel=False,
                phase='P0', tier=3, write_paths=['demo/forum/product/'],
                depends_on=list(dependencies), file=f'{fid}.md')


class CockpitAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = dict(schema_version=2, count=3,
                         features=[feature('001'), feature('002', ['001']), feature('003')])
        self.catalog = Catalog(self.data)
        self.path = self.root / 'state/factory.db'
        self.store = Store(self.path)

    def complete(self, fid, terminal=LIVE_COMPLETE):
        self.store.admit([fid], 'initial-' + fid, self.catalog)
        build = self.store.claim_next(self.catalog)
        self.store.complete_attempt(build['attempt_id'], build['attempt_generation'],
                                    {'simulated': terminal == SIMULATED_COMPLETE}, terminal=terminal)

    def test_a_real_completed_feature_cannot_be_admitted_after_restart(self):
        self.complete('001')
        reopened = Store(self.path)
        with self.assertRaisesRegex(StoreError, 'feature_already_completed:001'):
            reopened.admit(['001'], 'different-key', self.catalog)
        self.assertEqual(len(reopened.board()), 1)

    def test_a_merged_feature_is_locked(self):
        self.store.seed_merged('001', self.catalog)
        with self.assertRaisesRegex(StoreError, 'feature_already_completed:001'):
            self.store.admit(['001'], 'new-key', self.catalog)

    def test_a_simulation_does_not_count_as_implemented(self):
        self.complete('001', SIMULATED_COMPLETE)
        self.assertEqual(self.store.admit(['001'], 'real-request', self.catalog)['status'], 'admitted')

    def test_an_idempotent_replay_is_preserved(self):
        first = self.store.admit(['001'], 'same-key', self.catalog)
        second = self.store.admit(['001'], 'same-key', self.catalog)
        self.assertEqual(second['status'], 'replayed')
        self.assertEqual(first['build_ids'], second['build_ids'])

    def test_two_stores_cannot_queue_the_same_feature_concurrently(self):
        other = Store(self.path)
        def submit(pair):
            store, key = pair
            try:
                return store.admit(['001'], key, self.catalog)['status']
            except StoreError as error:
                return str(error)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(submit, [(self.store, 'first'), (other, 'second')]))
        self.assertCountEqual(outcomes, ['admitted', 'feature_in_progress:001'])
        self.assertEqual(len(self.store.board()), 1)

    def test_a_mixed_batch_rejection_does_not_create_other_builds(self):
        self.complete('001')
        with self.assertRaisesRegex(StoreError, 'feature_already_completed:001'):
            self.store.admit(['003', '001'], 'mixed', self.catalog)
        self.assertEqual(len(self.store.board()), 1)

    def app(self):
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(self.data))
        return FactoryApp(manifest, self.root / 'state', bootstrap_token='fixture-only')

    def test_catalog_distinguishes_built_dependency_and_available(self):
        self.complete('001')
        view = self.app().catalog_view(None)[1]
        features = {f['id']: f['availability'] for f in view['features']}
        self.assertEqual(features['001']['state'], 'built')
        self.assertFalse(features['001']['selectable'])
        self.assertEqual(features['002']['reason'], 'dependency_missing')
        self.assertTrue(features['003']['selectable'])

    def test_unsupported_target_is_not_selectable(self):
        app = self.app()
        app.execution_mode = 'live'
        # Presentation only; no target materialization or checker is invoked.
        from types import SimpleNamespace
        app.execution['target'] = SimpleNamespace(feature_id='001')
        view = app.catalog_view(None)[1]
        feature = next(f for f in view['features'] if f['id'] == '003')
        self.assertEqual(feature['availability']['reason'], 'target_unavailable')
        self.assertFalse(feature['availability']['selectable'])

    def test_api_refuses_a_completed_feature_with_conflict(self):
        self.complete('001')
        app = self.app()
        _, body, headers = app.login('127.0.0.1:8088', 'http://127.0.0.1:8088', {'token': 'fixture-only'})
        session = app.authenticate(headers['Set-Cookie'])
        with self.assertRaises(ApiError) as error:
            app.queue('127.0.0.1:8088', 'http://127.0.0.1:8088', session, body['csrf'],
                      {'ids': ['001'], 'idempotency_key': 'another-key'})
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(error.exception.code, 'feature_already_completed:001')

    def test_malformed_queue_values_are_refused_without_a_server_error(self):
        app = self.app()
        _, body, headers = app.login('127.0.0.1:8088', 'http://127.0.0.1:8088', {'token': 'fixture-only'})
        session = app.authenticate(headers['Set-Cookie'])
        for ids, key in [([{}], 'key'), (['001'], {'key': 1}), ([None], 'key')]:
            with self.subTest(ids=ids, key=key):
                with self.assertRaises(ApiError) as error:
                    app.queue('127.0.0.1:8088', 'http://127.0.0.1:8088', session, body['csrf'],
                              {'ids': ids, 'idempotency_key': key})
                self.assertEqual(error.exception.status, 400)
        self.assertEqual(app.store.board(), [])


if __name__ == '__main__':
    unittest.main()
