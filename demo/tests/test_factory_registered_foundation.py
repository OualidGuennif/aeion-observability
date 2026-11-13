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

    def prepare(self, reason="application_start_failed"):
        class Checker:
            def check_target(_,target,repo,frozen):
                return False,{'reason':reason}
        catalog=Catalog({'schema_version':2,'count':1,'features':[self.feature]})
        return TaskPreparer(self.root,self.source,role=self.role,checker=Checker(),base_ref='HEAD',product=True).prepare(
            build={'feature_id':self.feature['id'],'build_id':'a'*32,'attempt_id':'b'*32},catalog=catalog,spec_dir=self.specs,
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

    def test_a_registered_database_less_startup_rejection_is_a_negative_control(self):
        _,evidence=self.prepare('explicit_database_less_startup_rejected')
        self.assertEqual(evidence['negative_control'],'registered_foundation_startup_rejection')
        self.assertEqual(self.role.calls,[])

    def test_arbitrary_compiler_failure_is_never_a_registered_negative_control(self):
        with self.assertRaisesRegex(PreparationError,'negative_control_missing'):
            self.prepare('product_compile_failed')

    def test_missing_checker_reason_is_never_a_registered_negative_control(self):
        with self.assertRaisesRegex(PreparationError,'negative_control_missing'):
            self.prepare(None)

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

    def select_transition(self,feature):
        kind={'002':'postgres','003':'harness','014':'react'}[feature]
        shutil.copytree(ROOT/'demo/factory/transitions'/kind,self.root/'demo/factory/transitions'/kind)
        spec=next((ROOT/'demo/forum/features').glob(feature+'-*.md'))
        self.spec=self.specs/(feature+'.md');self.spec.write_bytes(spec.read_bytes())
        self.feature.update(id=feature,file=self.spec.name)
        if feature=='014':self.feature['write_paths'].append('demo/forum-web/')
        else:
            original=(ROOT/'demo/forum-app/build.gradle').read_bytes()
            (self.source/'demo/forum-app/build.gradle').write_bytes(original)
            subprocess.run(['git','-C',str(self.source),'add','.'],check=True,capture_output=True)
            subprocess.run(['git','-C',str(self.source),'commit','-qm','public transition baseline'],check=True,capture_output=True)

    def test_harness_transition_uses_registered_acceptance_without_model_or_cost(self):
        self.select_transition('003')
        target,evidence=self.prepare('registered_harness_oracle_failed')
        self.assertEqual(evidence['negative_control'],'registered_transition_source_missing')
        self.assertEqual(evidence['preparation_kind'],'registered_static_acceptance')
        self.assertEqual(self.role.calls,[])
        self.assertIsNone(evidence['preparer_model'])
        self.assertEqual(target.feature_id,'003')
        catalog=Catalog({'schema_version':2,'count':1,'features':[self.feature]})
        store=Store(self.root/'factory-harness.db');store.admit(['003'],'registered',catalog)
        build=store.claim_next(catalog)
        self.assertTrue(store.record_preparation(build['attempt_id'],build['attempt_generation'],evidence))

    def test_harness_transition_refuses_arbitrary_compile_failure(self):
        self.select_transition('003')
        with self.assertRaisesRegex(PreparationError,'negative_control_missing'):
            self.prepare('product_compile_failed')

    def test_postgres_transition_freezes_dependencies_without_granting_worker_verifier_control(self):
        self.select_transition('002')
        target,evidence=self.prepare('registered_postgres_operator_missing')
        self.assertEqual(evidence['negative_control'],'registered_transition_source_missing')
        self.assertEqual(self.role.calls,[])
        self.assertEqual(len(target.dependency_changes),1)
        self.assertIn('demo/forum-app/build.gradle',target.write_paths)
        self.assertFalse(any(path.startswith(('tools/','.github/')) for path in target.write_paths))

    def test_web_transition_seeds_only_the_exact_frozen_dependency_pair(self):
        self.select_transition('014')
        target,evidence=self.prepare('registered_web_source_missing')
        self.assertEqual(evidence['negative_control'],'registered_transition_source_missing')
        self.assertEqual(self.role.calls,[])
        self.assertEqual({name for name,_ in target.dependency_changes},
            {'demo/forum-web/package.json','demo/forum-web/package-lock.json'})

    def test_transition_compiler_failure_does_not_qualify_a_registered_absence(self):
        self.select_transition('014')
        with self.assertRaisesRegex(PreparationError,'negative_control_missing'):
            self.prepare('product_compile_failed')

if __name__=='__main__':unittest.main()
