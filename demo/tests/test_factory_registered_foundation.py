"""Registered acceptance is spec-bound and spends no model calls; changed MDs fall back."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import subprocess

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'demo'))
from factory.preparation import TaskPreparer, PreparationError
from factory.manifest import Catalog
from factory.budget import DailyBudget
from factory.models import Router
from factory.store import Store,StoreError
from test_factory_preparation import ScriptedRole

class RegisteredFoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        architecture=self.root/'demo/forum/ARCHITECTURE.md';architecture.parent.mkdir(parents=True)
        architecture.write_bytes((ROOT/'demo/forum/ARCHITECTURE.md').read_bytes())
        self.specs=self.root/'specs';self.specs.mkdir()
        self.spec=self.specs/'001.md';self.spec.write_bytes(next((ROOT/'demo/forum/features').glob('001-*.md')).read_bytes())
        shutil.copytree(ROOT/'demo/factory/transitions/foundation',self.root/'demo/factory/transitions/foundation')
        self.source=self.root/'source';(self.source/'demo/forum-app').mkdir(parents=True)
        (self.source/'demo/forum-app/build.gradle').write_text('// Public fixture\n')
        for args in (['init','-q'],['config','user.name','Fixture'],['config','user.email','fixture@example.invalid'],
                     ['add','.'],['commit','-qm','public baseline']):
            subprocess.run(['git','-C',str(self.source),*args],check=True,capture_output=True)
        self.role=ScriptedRole();self.budget=DailyBudget(self.root/'ledger.jsonl')
        self.feature={'id':'001','title':'App skeleton','area':'foundation','size':'S','phase':'P0',
            'tier':3,'parallel':False,'depends_on':[],'write_paths':['demo/forum-app/'],'file':'001.md',
            'architecture_digest':hashlib.sha256(architecture.read_bytes()).hexdigest()}

    def prepare(self):
        class Checker:
            def check_target(_,target,repo,frozen):
                return False,{'reason':'application_start_failed'}
        catalog=Catalog({'schema_version':2,'count':1,'features':[self.feature]})
        return TaskPreparer(self.root,self.source,role=self.role,checker=Checker(),base_ref='HEAD',product=True).prepare(
            build={'feature_id':'001','build_id':'a'*32,'attempt_id':'b'*32},catalog=catalog,spec_dir=self.specs,
            destination=self.root/'prepared',budget=self.budget,router=Router(),authorized=lambda:True)

    def test_known_spec_uses_registered_acceptance_without_model_or_cost(self):
        self.role.last_execution = {'forwarded_count': 3, 'model': 'qwen-3.8-flash'}
        target,evidence=self.prepare()
        self.assertEqual(target.protected_check.id,'prepared_product')
        self.assertEqual(self.role.calls,[])
        self.assertIsNone(evidence['preparer_model'])
        self.assertIsNone(self.role.last_execution)
        self.assertEqual(evidence['preparation_kind'],'registered_static_acceptance')
        self.assertEqual(self.budget.spent('aeion-autonomous-forum'),0)
        self.assertTrue(evidence['synthetic'])  # Unit checker/role are synthetic, not activation evidence.

    def test_registered_task_persists_without_inventing_a_preparer_model(self):
        _,evidence=self.prepare()
        catalog=Catalog({'schema_version':2,'count':1,'features':[self.feature]})
        store=Store(self.root/'factory.db');store.admit(['001'],'registered',catalog)
        build=store.claim_next(catalog)
        self.assertTrue(store.record_preparation(build['attempt_id'],build['attempt_generation'],evidence))
        saved=json.loads(store.by_attempt(build['attempt_id'])['receipt'])['preparation']
        self.assertEqual(saved,evidence)
        for changed in ({**evidence,'preparer_model':'glm-5.3-flash'},
                        {**evidence,'write_paths':['tools/agents/']}):
            with self.assertRaisesRegex(StoreError,'invalid_preparation_evidence'):
                store.record_preparation(build['attempt_id'],build['attempt_generation'],changed)

    def test_modified_md_cannot_reuse_the_old_registered_oracle(self):
        self.spec.write_text(self.spec.read_text()+'\nAdditional acceptance: authenticated health.\n')
        with self.assertRaisesRegex(PreparationError,'runtime_mismatch'):self.prepare()
        self.assertEqual(len(self.role.calls),1)
        self.assertTrue((self.root/'prepared/proposed-acceptance.json').is_file())

if __name__=='__main__':unittest.main()
