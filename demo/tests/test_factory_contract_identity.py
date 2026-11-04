"""Versioned completion must prove the current MD, not just a historical feature ID."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog, load_manifest
from factory.store import Store, StoreError, SCHEMA
from factory.preparation import freeze_task, PreparationError


class ContractIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.specs = self.root / 'features'
        self.specs.mkdir()
        architecture = b'Approved architecture\n'
        (self.root / 'ARCHITECTURE.md').write_bytes(architecture)
        self.raw = {'schema_version': 2, 'count': 2, 'architecture': 'test-v1',
                    'architecture_digest': hashlib.sha256(architecture).hexdigest(), 'features': []}
        for fid, deps in [('001', []), ('002', ['001'])]:
            self.raw['features'].append({'id': fid, 'file': fid+'.md', 'title': fid,
                'area': 'foundation', 'size': 'S', 'parallel': False, 'phase': 'P0',
                'tier': 3, 'write_paths': ['demo/forum-app/'], 'depends_on': deps,
                'architecture_digest': self.raw['architecture_digest']})
            (self.specs / (fid+'.md')).write_text('# '+fid+'\nOriginal acceptance\n')
        self.manifest = self.specs / 'MANIFEST.json'
        self.manifest.write_text(json.dumps(self.raw))
        self.catalog = load_manifest(self.manifest)
        self.store = Store(self.root / 'state.db')

    def rewrite(self, fid):
        (self.specs / (fid+'.md')).write_text('# '+fid+'\nChanged acceptance\n')
        return load_manifest(self.manifest)

    def test_rewritten_md_is_selectable_but_does_not_inherit_old_dependency_evidence(self):
        self.store.seed_merged('001', self.catalog)
        changed = self.rewrite('001')
        states = self.store.feature_availability(changed)
        self.assertEqual(states['001']['state'], 'ready')
        self.assertEqual(states['002']['missing_dependencies'], ['001'])
        admitted = self.store.admit(['001'], 'new-contract', changed)
        self.assertEqual(admitted['status'], 'admitted')
        self.assertEqual(len(self.store.board()), 2)

    def test_unrelated_md_edit_preserves_completion_and_pending_request(self):
        self.store.seed_merged('001', self.catalog)
        changed = self.rewrite('002')
        self.assertEqual(self.store.feature_availability(changed)['001']['state'], 'implemented')
        with self.assertRaisesRegex(StoreError, 'feature_already_completed'):
            self.store.admit(['001'], 'repeat', changed)
        self.store.admit(['002'], 'launch', changed)
        raw = copy.deepcopy(self.raw)
        raw['features'][0]['title'] = 'Unrelated display edit'
        # The pending feature's own contract is unchanged; its dependency needs requalification.
        self.manifest.write_text(json.dumps(raw))
        newer = load_manifest(self.manifest)
        self.assertIsNone(self.store.claim_next(newer))
        pending = self.store.board()[-1]
        self.assertEqual(pending['hold_reason'], 'dependency_missing')

    def test_disk_edit_after_admission_holds_before_any_attempt(self):
        self.store.admit(['001'], 'launch', self.catalog)
        self.rewrite('001')
        self.assertIsNone(self.store.claim_next(self.catalog))
        self.assertEqual(self.store.board()[0]['hold_reason'], 'catalog_changed')
        self.assertIsNone(self.store.board()[0]['attempt_id'])

    def test_preparation_checks_the_captured_bytes_not_only_an_earlier_path_read(self):
        # Simulate an editor swapping the MD only during the preparer's actual read.
        with patch('factory.preparation._read',side_effect=['# Different captured MD\n','Approved architecture\n']):
            with self.assertRaisesRegex(PreparationError,'preparation_contract_changed'):
                freeze_task(self.catalog,'001',self.specs,self.root/'ARCHITECTURE.md','a'*40)

    def test_explicit_new_admission_retires_only_obsolete_no_attempt_request(self):
        first = self.store.admit(['001'], 'old', self.catalog)
        changed = self.rewrite('001')
        self.store.admit(['001'], 'new', changed)
        old, new = self.store.board()
        self.assertEqual(old['build_id'], first['build_ids'][0])
        self.assertEqual(old['status'], 'cancelled')
        self.assertEqual(new['status'], 'queued')
        self.assertIn('superseded_contract', [e['event'] for e in self.store.events(old['build_id'])])

    def test_uncertain_old_attempt_still_blocks_new_contract(self):
        self.store.admit(['001'], 'old', self.catalog)
        attempt = self.store.claim_next(self.catalog)
        self.store.hold_dispatched(attempt['build_id'], 'worker_error')
        changed = self.rewrite('001')
        with self.assertRaisesRegex(StoreError, 'feature_in_progress'):
            self.store.admit(['001'], 'new', changed)
        self.assertFalse(self.store.feature_availability(changed)['001']['selectable'])

    def test_late_old_merge_does_not_certify_a_rewritten_md_and_both_versions_survive(self):
        self.store.admit(['001'],'old',self.catalog)
        old=self.store.claim_next(self.catalog)
        def stage(build):
            request={k:build[k] for k in ('build_id','attempt_id','attempt_generation')}
            self.assertTrue(self.store.stage_publication(build,request,{}))
            return self.store.claim_publication()
        job=stage(old)
        self.store.cancel(old['build_id'])
        changed=self.rewrite('001')
        result={'status':'merged','confirmed_main':True,'merge_sha':'a'*40,'main_sha':'b'*40}
        self.store.finish_publication(job,result,simulated=False)
        self.assertEqual(self.store.feature_availability(changed)['001']['state'],'ready')
        self.assertEqual(self.store.feature_availability(changed)['002']['missing_dependencies'],['001'])
        self.store.admit(['001'],'new',changed)
        new=self.store.claim_next(changed)
        self.store.finish_publication(stage(new),{**result,'merge_sha':'c'*40,'main_sha':'d'*40},simulated=False)
        self.assertEqual(self.store.feature_availability(changed)['001']['state'],'implemented')
        with sqlite3.connect(self.store.path) as conn:
            identities=conn.execute('SELECT contract_digest FROM feature_integrations WHERE feature_id=?',('001',)).fetchall()
        self.assertEqual({r[0] for r in identities},{self.catalog.contracts['001'],changed.contracts['001']})

    def test_symlink_swap_cannot_keep_a_completed_contract_current(self):
        self.store.seed_merged('001',self.catalog)
        original=self.specs/'001.md'
        moved=self.root/'same-bytes.md'
        original.rename(moved);original.symlink_to(moved)
        states=self.store.feature_availability(self.catalog)
        self.assertEqual(states['001']['reason'],'catalog_changed')
        self.assertFalse(states['001']['selectable'])

    def test_old_completion_without_contract_is_history_not_current_proof(self):
        self.store.seed_merged('001', self.catalog)
        with sqlite3.connect(self.store.path) as conn:
            conn.execute("UPDATE builds SET contract_digest='' WHERE feature_id='001'")
        reopened = Store(self.store.path)
        self.assertEqual(reopened.board()[0]['status'], 'merged')
        self.assertEqual(reopened.feature_availability(self.catalog)['001']['state'], 'ready')

    def test_legacy_baseline_cannot_certify_new_contract(self):
        with self.assertRaisesRegex(StoreError, 'baseline_contract_unqualified'):
            self.store.record_baseline('001', {'base_sha': 'a'*40}, self.catalog)

    def test_unrelated_catalog_change_does_not_revoke_unchanged_queued_contract(self):
        self.store.admit(['001'], 'launch', self.catalog)
        changed = self.rewrite('002')
        self.assertIsNotNone(self.store.claim_next(changed))

    def test_legacy_database_migration_preserves_rows_without_inventing_contracts(self):
        path = self.root / 'legacy.db'
        legacy = SCHEMA.replace("  contract_digest TEXT NOT NULL DEFAULT '',\n", '')
        legacy = legacy.replace('  feature_id TEXT NOT NULL,\n  contract_digest TEXT NOT NULL,\n',
                                '  feature_id TEXT PRIMARY KEY,\n')
        legacy = legacy.replace('  observed_ns INTEGER NOT NULL,\n  PRIMARY KEY(feature_id, contract_digest)',
                                '  observed_ns INTEGER NOT NULL')
        with sqlite3.connect(path) as conn:
            conn.executescript(legacy)
            conn.execute('INSERT INTO feature_integrations VALUES(?,?,?,?,?)',
                         ('001','historical-attempt','a'*40,'b'*40,42))
        migrated = Store(path)
        Store(path)  # Schema migration is restart-idempotent.
        with sqlite3.connect(path) as conn:
            row = conn.execute('SELECT feature_id,contract_digest,attempt_id,merge_sha,main_sha,observed_ns '
                               'FROM feature_integrations').fetchone()
        self.assertEqual(row, ('001','','historical-attempt','a'*40,'b'*40,42))
        self.assertEqual(migrated.feature_availability(self.catalog)['001']['state'], 'ready')


if __name__ == '__main__':
    unittest.main()
