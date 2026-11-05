"""The old incomplete review envelope gets one fenced reassessment, never a vote override."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import subprocess
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import Store
from factory.dispatch import DispatchWorker
from factory.preparation import TaskPreparer,freeze_task
from factory.product_checks import prepared_target
from factory.freeze import freeze_build
from factory.artifact import validate_artifact
from factory.budget import DailyBudget
from factory.review_circuit import CircuitError


class ReviewContextClaimTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'factory.db')
        self.catalog=Catalog({'schema_version':2,'count':1,'features':[{
            'id':'001','title':'Fixture','area':'foundation','size':'S','parallel':False,
            'phase':'P0','tier':3,'write_paths':['demo/forum/product/'],'depends_on':[],'file':'001.md'}]})
        self.store.admit(['001'],'fixture',self.catalog)
        self.build=self.store.claim_next(self.catalog)
        self.receipt={'simulated':False,'author_model':'glm-5.3-flash','artifact_digest':'a'*64,
            'gate':{'status':'passed'},'review':{'status':'approved'},
            'execution':{'build_id':self.build['build_id'],'role':'author','engine':'flue-pi',
                'forwarded_count':1,'usage':{'complete':True,'cost_usd':'0.10'}},
            'circuit':{'status':'held','reason':'reviewer_rejected','votes':[{
                'model':'qwen-3.8-flash','verdict':'reject','reason':'Synthetic fixture',
                'execution':{'role':'review','engine':'flue-pi','forwarded_count':1,
                    'usage':{'complete':True,'cost_usd':'0.01'}}}]}}

    def hold(self,receipt):
        self.store.hold_dispatched(self.build['build_id'],'owner_review_required',receipt=receipt)
        row=self.store.board()[0]
        return hashlib.sha256(row['receipt'].encode()).hexdigest()

    def test_reassessment_preserves_rejection_and_fences_duplicate_and_old_callbacks(self):
        digest=self.hold(self.receipt)
        claimed=self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12)
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed['attempt_generation'],self.build['attempt_generation']+1)
        self.assertFalse(self.store.attempt_authorized(self.build['attempt_id'],self.build['attempt_generation']))
        self.assertTrue(self.store.attempt_authorized(claimed['attempt_id'],claimed['attempt_generation']))
        self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12))

        events=self.store.events(self.build['build_id'])
        event=next(x for x in events if x['event']=='review_context_reassessment')
        self.assertEqual(json.loads(event['detail'])['previous_receipt'],self.receipt)
        self.store.hold_dispatched(claimed['build_id'],'owner_review_required',receipt=json.loads(claimed['receipt']))
        digest=hashlib.sha256(self.store.board()[0]['receipt'].encode()).hexdigest()
        self.assertIsNone(self.store.claim_review_context(claimed['build_id'],self.catalog,digest,10**12))

    def test_missing_usage_new_format_and_changed_receipts_never_rearm(self):
        for path,value in [(('execution','usage','complete'),False),
                           (('execution','failure'),'EXPORT_FAILED'),
                           (('circuit','review_input_version'),2),
                           (('simulated',),True), (('gate','status'),'failed')]:
            with self.subTest(path=path):
                receipt=copy.deepcopy(self.receipt);item=receipt
                for key in path[:-1]:item=item[key]
                item[path[-1]]=value
                digest=self.hold(receipt)
                self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12))
                # Restore the dispatched fixture through a new independent temporary store.
                self.setUp()
        digest=self.hold(self.receipt)
        self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,'0'*64,10**12))
        self.store.cancel(self.build['build_id'])
        self.assertIsNone(self.store.claim_review_context(self.build['build_id'],self.catalog,digest,10**12))


class ReviewContextDispatchTests(unittest.TestCase):
    """Git/files/state are real; model and isolated checker transports are scripted fixtures."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        architecture=self.root/'demo/forum/ARCHITECTURE.md';architecture.parent.mkdir(parents=True)
        architecture.write_text('Incremental PostgreSQL and React architecture.\n')
        specs=self.root/'specs';specs.mkdir();(specs/'001.md').write_text('# 001\n## Acceptance checks\n- [ ] Bound settings.\n')
        self.catalog=Catalog({'schema_version':2,'count':1,'features':[{
            'id':'001','title':'Settings','area':'foundation','size':'S','phase':'P0','parallel':False,
            'tier':3,'file':'001.md','write_paths':['demo/forum-app/'],'depends_on':[],
            'architecture_digest':hashlib.sha256(architecture.read_bytes()).hexdigest()}]})
        source=self.root/'source';path=source/'demo/forum-app/src/main/resources/settings.properties'
        path.parent.mkdir(parents=True);path.write_text('database=sqlite\nlimit=1\n')
        for args in (['init','-q'],['add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                    'commit','-qm','base']):
            subprocess.run(['git','-C',str(source),*args],capture_output=True,check=True)
        self.base=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
        self.store=Store(self.root/'factory.db');self.store.admit(['001'],'fixture',self.catalog)
        self.build=self.store.claim_next(self.catalog);folder=self.root/'work'/self.build['build_id']
        prepared=folder/'prepared';prepared.mkdir(parents=True)
        task=freeze_task(self.catalog,'001',specs,architecture,self.base,product=True)
        acceptance='Synthetic fixture contract; the checker transport is scripted.\n'
        target=prepared_target(self.root,source,task,prepared,acceptance)
        target.materialize(folder/'repo')
        self.file=folder/'repo/demo/forum-app/src/main/resources/settings.properties'
        self.file.write_text('database=sqlite\nlimit=2\n')
        (folder/'BRIEF.md').write_text(task.specification)
        self.config={'profile':'fixture','mode':'live','deadline_ns':1800*10**9,'step_cap':200,
            'context_limit':250000,'cost_reservation_usd':'0.50'}
        frozen=freeze_build(self.build,self.catalog,specs,self.base,self.config,
            write_scopes=target.write_paths,spec_path=target.brief,acceptance_path=target.protected_check.contract_test)
        artifact=validate_artifact(folder/'repo',frozen.write_scopes)
        execution={'build_id':self.build['build_id'],'role':'author','engine':'flue-pi',
            'forwarded_count':1,'usage':{'complete':True,'cost_usd':'0.10'}}
        self.prior={'simulated':False,'author_model':'glm-5.3-flash','execution':execution,
            'base_sha':self.base,'frozen_digest':frozen.digest(),'artifact_digest':artifact['digest'],
            'preparation':{**task.identity(),'task_digest':task.digest(),'synthetic':False,
                'acceptance_digest':frozen.acceptance_digest,'preparer_model':None},
            'gate':{'status':'passed'},'review':{'status':'approved'},
            'circuit':{'status':'held','reason':'reviewer_rejected','votes':[{
                'model':'qwen-3.8-flash','verdict':'reject','execution':{**execution,'role':'review'}}]}}
        self.store.hold_dispatched(self.build['build_id'],'owner_review_required',receipt=self.prior)
        self.checks=[];self.votes=[];self.requests=[]
        checker=SimpleNamespace(check_target=lambda target,repo,frozen:
            (self.checks.append(str(repo)) or True,{'reason':'passed'}))
        outer=self
        class Reviewer:
            paid=True;timeout_seconds=60;cost_limit='0.10';last_usage=None;last_execution=None
            def __call__(self,model,prompt):
                self.last_usage={'complete':True,'cost_usd':'0.01'}
                self.last_execution={'role':'review','engine':'flue-pi','forwarded_count':1,'usage':self.last_usage}
                outer.votes.append((model,prompt))
                if model==outer.failure_model:
                    self.last_execution['failure']='REVIEW_RESULT_MISSING'
                    if outer.unknown_failure_usage:self.last_usage['complete']=False
                    raise ValueError('REVIEW_RESULT_MISSING')
                return {'verdict':outer.verdict,'reason':'Synthetic fixture'}
        self.verdict='approve'
        self.failure_model=None
        self.unknown_failure_usage=False
        self.budget=DailyBudget(self.root/'ledger.jsonl')
        self.worker=DispatchWorker(self.store,self.catalog,specs,self.root/'work',self.config,
            builder=SimpleNamespace(paid=True,engine='flue-pi',last_execution=None),
            preparer=TaskPreparer(self.root,source,product=True,synchronize=lambda:self.base),
            check_sandbox=checker,review_complete=Reviewer(),budget=self.budget)
        self.worker.admission_check=lambda:True
        self.worker.publication=SimpleNamespace(stage=lambda build,request,receipt:
            self.requests.append((request,receipt)) or True)

    def test_reassessment_reruns_gate_and_two_fresh_votes_without_author_or_double_charge(self):
        result=self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(result['result']['status'],'publication_queued')
        self.assertEqual(len(self.checks),1)
        self.assertEqual([m for m,_ in self.votes],['qwen-3.8-flash','deepseek-4.1-flash'])
        self.assertTrue(all('-limit=1\n+limit=2' in p for _,p in self.votes))
        request,receipt=self.requests[0]
        self.assertEqual(receipt['execution'],self.prior['execution'])
        self.assertTrue(receipt['review_context']['author_reused'])
        self.assertEqual(request['artifact_digest'],self.prior['artifact_digest'])
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.02')

    def test_changed_artifact_or_base_refuses_before_models_or_rearming(self):
        self.file.write_text('changed after original review\n')
        with self.assertRaisesRegex(CircuitError,'artifact_changed'):
            self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(self.votes,[]);self.assertEqual(self.store.board()[0]['status'],'held')
        self.worker.preparer.synchronize=lambda:'f'*40
        with self.assertRaisesRegex(CircuitError,'base_changed'):
            self.worker.reassess_review_context(self.build['build_id'])

    def test_a_fresh_rejection_stays_held_and_cannot_be_repeated_as_context_repair(self):
        self.verdict='reject'
        self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(self.requests,[])
        self.assertEqual(self.store.board()[0]['status'],'held')
        with self.assertRaisesRegex(CircuitError,'not_eligible'):
            self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(len(self.votes),1)
        with self.assertRaisesRegex(CircuitError,'not_eligible'):
            self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(len(self.votes),1)

    def test_one_failed_review_retry_rechecks_and_replaces_both_votes_without_rerunning_author(self):
        self.failure_model='deepseek-4.1-flash'
        self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(self.requests,[])
        self.assertEqual([m for m,_ in self.votes],['qwen-3.8-flash','deepseek-4.1-flash'])
        self.failure_model=None
        result=self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(result['result']['status'],'publication_queued')
        self.assertEqual([m for m,_ in self.votes][-2:],['deepseek-4.1-flash','qwen-3.8-flash'])
        self.assertEqual(len(self.checks),2)
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.04')
        self.assertEqual(self.requests[0][1]['execution'],self.prior['execution'])

    def test_a_second_failed_review_stays_held_without_an_unbounded_retry(self):
        self.failure_model='deepseek-4.1-flash'
        self.worker.reassess_review_context(self.build['build_id'])
        self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(len(self.votes),3)
        self.assertEqual(self.requests,[])
        with self.assertRaisesRegex(CircuitError,'not_eligible'):
            self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(len(self.votes),3)

    def test_retry_does_not_free_an_old_unknown_review_reservation(self):
        self.failure_model='deepseek-4.1-flash';self.unknown_failure_usage=True
        self.worker.reassess_review_context(self.build['build_id'])
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.11')
        self.failure_model=None
        self.worker.reassess_review_context(self.build['build_id'],retry_failed_review=True)
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')),'0.13')


if __name__=='__main__':unittest.main()
