"""Outbox staging, lease ownership, CI waiting and main confirmation are durable transitions."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import Store,StoreError,FAILED,GATED,HELD,PR_OPEN,QUEUED,MERGED
from factory.publication import PublicationCoordinator
from factory.review import content_digest
from factory.publisher import verified_receipt


class FakeRoles:
 real=False
 def __init__(self):self.calls=[]
 def __call__(self,job):
  self.calls.append(job['phase'])
  if job['phase']=='publish':return {'status':'published','pr':{'pr_number':7,'head_sha':'b'*40,'simulated':True}}
  return {'status':'merged','merge_sha':'c'*40,'main_sha':'c'*40,'confirmed_main':True}


class PublicationStateTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
  self.store=Store(Path(self.folder.name)/'state.db')
  self.catalog=Catalog({'schema_version':2,'count':1,'features':[{'id':'082','title':'Docs','area':'corpus',
   'size':'S','phase':'P0','parallel':False,'tier':3,'write_paths':['demo/forum-docs/'],'depends_on':[],'file':'082.md'}]})
  self.store.admit(['082'],'fixture',self.catalog);self.build=self.store.claim_next(self.catalog)
  files={'demo/forum-docs/x.md':'Synthetic text'};digest=content_digest(files)
  self.receipt={'simulated':True,'gate':{'status':'passed'},'review':{'status':'approved'},
   'circuit':{'status':'approved','author_model':'glm-5.3-flash','votes':[
    {'model':'qwen-3.8-flash','family':'qwen','verdict':'approve'},
    {'model':'claude-haiku-5.5','family':'anthropic','verdict':'approve'}]}}
  self.request={'attempt_id':self.build['attempt_id'],'build_id':self.build['build_id'],
   'attempt_generation':self.build['attempt_generation'],'target_repo':'o/r','files':files,'artifact_digest':digest}
  self.roles=FakeRoles();self.coordinator=PublicationCoordinator(self.store,self.roles,repo='o/r')

 def stage(self):self.assertTrue(self.coordinator.stage(self.build,self.request,self.receipt))

 def test_expired_worker_lease_cannot_stage_a_future_remote_effect(self):
  self.store._now=lambda:self.build['lease_until_ns']
  self.assertFalse(self.coordinator.stage(self.build,self.request,self.receipt))
  self.assertIsNone(self.store.publication_request(self.build['attempt_id']))

 def test_known_tree_permission_refusal_can_resume_without_rebuilding_or_model_calls(self):
  self.stage();job=self.store.claim_publication()
  self.store.finish_publication(job,{'status':'held','reason':'tree_create_failed:403'})
  self.assertTrue(self.store.resume_denied_publication(self.request))
  resumed=self.store.claim_publication()
  self.assertEqual(resumed['phase'],'publish')
  self.assertEqual(resumed['request'],self.request)
  self.assertEqual(resumed['attempt_id'],job['attempt_id'])

 def test_a_failed_required_check_queues_one_correction_and_other_holds_do_not(self):
  self.receipt={**self.receipt,'artifact_digest':self.request['artifact_digest'],
                'feedback':{'author':'hibernate stays lazy','reviewers':[{'model':'glm-5.3-flash','text':'port 8081'}]}}
  self.stage();job=self.store.claim_publication()
  self.store.finish_publication(job,{'status':'held','reason':'ci_failed','failed_checks':[
      {'name':'Product artifacts','conclusion':'failure'}]},delay_ns=0)
  result=self.store.continue_after_ci_failure(self.build['build_id'],self.catalog,self.request['files'])
  self.assertEqual(result['status'],'failed')
  self.assertEqual((result['correction']['attempt'],result['correction']['round']),(1,1))
  first,second=self.store.board()
  self.assertEqual(first['status'],FAILED)
  marker=json.loads(first['receipt'])['correction']
  self.assertEqual(marker['trigger'],'ci_failed')
  self.assertEqual(marker['candidate_files'],['demo/forum-docs/x.md'])
  self.assertEqual(marker['candidate_digest'],self.request['artifact_digest'])
  self.assertEqual(json.loads(first['receipt'])['publisher']['failed_checks'][0]['name'],'Product artifacts')
  self.assertEqual(second['status'],QUEUED)
  self.assertEqual(self.store.correction_of(second['build_id']),
                   {'previous_build_id':first['build_id'],'attempt':1,'round':1})
  self.assertEqual(self.store.continue_after_ci_failure(
      self.build['build_id'],self.catalog,self.request['files'])['status'],'unchanged')
  self.assertEqual(len(self.store.board()),2)

 def test_an_unreadable_or_permission_hold_is_not_a_correction(self):
  for reason in ('ci_unreadable','tree_create_failed:403','protection_unqualified'):
   with self.subTest(reason=reason):
    self.setUp();self.stage();job=self.store.claim_publication()
    self.store.finish_publication(job,{'status':'held','reason':reason},delay_ns=0)
    result=self.store.continue_after_ci_failure(self.build['build_id'],self.catalog,self.request['files'])
    self.assertEqual(result['status'],'unchanged')
    self.assertEqual(self.store.board()[0]['status'],HELD)
    self.assertEqual(len(self.store.board()),1)

 def test_the_last_ci_failure_stays_held_for_the_owner(self):
  self.stage();job=self.store.claim_publication()
  self.store.finish_publication(job,{'status':'held','reason':'ci_failed'},delay_ns=0)
  with self.store._connect() as conn:
   conn.execute("INSERT INTO events (build_id,time_ns,actor,event,detail,generation) VALUES (?,?,?,?,?,?)",
                (self.build['build_id'],1,'supervisor','correction',
                 json.dumps({'previous_build_id':'a'*32,'attempt':3,'round':2}),0))
  result=self.store.continue_after_ci_failure(self.build['build_id'],self.catalog,{})
  self.assertEqual(result,{'status':'held','reason':'ci_failed','exhausted':True})
  row=self.store.board()[0]
  self.assertEqual(row['status'],HELD)
  self.assertTrue(json.loads(row['receipt'])['correction']['exhausted'])
  self.assertEqual(len(self.store.board()),1)

 def test_denial_resume_refuses_unknown_effect_changed_request_and_cancellation(self):
  self.stage();job=self.store.claim_publication()
  self.store.finish_publication(job,{'status':'held','reason':'forge_reconciliation_required'})
  self.assertFalse(self.store.resume_denied_publication(self.request))
  # A fixed403 alone is insufficient when the frozen payload or generation changed.
  with self.store._connect() as conn:
   receipt=json.loads(conn.execute('SELECT receipt FROM builds WHERE attempt_id=?',(self.build['attempt_id'],)).fetchone()['receipt'])
   receipt['publisher']={'status':'held','reason':'tree_create_failed:403'}
   conn.execute('UPDATE builds SET receipt=? WHERE attempt_id=?',(json.dumps(receipt),self.build['attempt_id']))
  changed={**self.request,'artifact_digest':'f'*64}
  self.assertFalse(self.store.resume_denied_publication(changed))
  self.store.cancel(self.build['build_id'])
  self.assertFalse(self.store.resume_denied_publication(self.request))

 def test_atomic_stage_survives_restart_and_keeps_the_feature_active(self):
  self.stage();new=Store(self.store.path)
  self.assertEqual(new.board()[0]['status'],GATED)
  self.assertEqual(new.publication_request(self.build['attempt_id']),self.request)
  self.assertIsNone(new.claim_next(self.catalog))

 def test_publish_ci_and_main_are_distinct_and_simulation_never_becomes_merged(self):
  self.stage();job=self.store.claim_publication()
  self.store.finish_publication(job,self.roles(job),simulated=True,delay_ns=0)
  self.assertEqual(self.store.board()[0]['status'],PR_OPEN)
  result=self.coordinator.run_once()
  self.assertEqual(result['result']['status'],'simulated_complete')
  self.assertNotEqual(self.store.board()[0]['status'],MERGED)

 def test_two_publishers_cannot_claim_the_same_lease(self):
  self.stage();first=self.store.claim_publication()
  self.assertIsNotNone(first)
  self.assertIsNone(Store(self.store.path).claim_publication())

 def test_cancel_revokes_next_effect_and_late_response_cannot_revive_attempt(self):
  self.stage();job=self.store.claim_publication()
  self.assertTrue(self.store.publication_authorized(job['attempt_id'],job['generation'],job['lease_owner']))
  self.store.cancel(self.build['build_id'])
  self.assertFalse(self.store.publication_authorized(job['attempt_id'],job['generation'],job['lease_owner']))
  self.store.finish_publication(job,{'status':'published'},simulated=True)
  self.assertEqual(self.store.board()[0]['status'],'cancelled')

 def test_missing_main_confirmation_cannot_mark_a_real_merge(self):
  self.stage();job=self.store.claim_publication()
  self.store.finish_publication(job,{'status':'merged'},simulated=False)
  row=self.store.board()[0]
  self.assertEqual(row['status'],'held')
  self.assertEqual(json.loads(row['receipt'])['publisher']['reason'],'merge_not_confirmed')

 def test_cancelled_publication_blocks_duplicate_launch_while_remote_effect_is_unknown(self):
  self.stage();self.store.claim_publication()
  self.store.cancel(self.build['build_id'])
  reopened=Store(self.store.path)
  with self.assertRaisesRegex(StoreError,'publication_reconciliation_required'):
   reopened.admit(['082'],'duplicate',self.catalog)
  availability=reopened.feature_availability(self.catalog)['082']
  self.assertFalse(availability['selectable'])
  self.assertEqual(availability['reason'],'reconciliation_needed')

 def test_late_confirmed_real_merge_locks_feature_without_reviving_cancelled_attempt(self):
  self.stage();job=self.store.claim_publication()
  self.store.cancel(self.build['build_id'])
  self.store.finish_publication(job,{'status':'merged','confirmed_main':True,
   'merge_sha':'c'*40,'main_sha':'d'*40},simulated=False)
  reopened=Store(self.store.path)
  self.assertEqual(reopened.board()[0]['status'],'cancelled')
  self.assertEqual(reopened.feature_availability(self.catalog)['082']['state'],'implemented')
  with self.assertRaisesRegex(StoreError,'feature_already_completed'):
   reopened.admit(['082'],'duplicate',self.catalog)

 def test_late_synthetic_or_unconfirmed_merge_never_implements_a_feature(self):
  self.stage();job=self.store.claim_publication()
  self.store.cancel(self.build['build_id'])
  self.store.finish_publication(job,{'status':'merged','confirmed_main':True,
   'merge_sha':'c'*40,'main_sha':'d'*40},simulated=True)
  self.assertNotEqual(self.store.feature_availability(self.catalog)['082']['state'],'implemented')

 def test_expired_publisher_lease_can_be_reconciled_without_rebuilding(self):
  self.stage();first=self.store.claim_publication(lease_ns=0)
  next_job=self.store.claim_publication()
  self.assertEqual(first['attempt_id'],next_job['attempt_id'])
  self.assertNotEqual(first['lease_owner'],next_job['lease_owner'])
  self.assertFalse(self.store.publication_authorized(first['attempt_id'],first['generation'],first['lease_owner']))

 def test_only_complete_bound_real_receipt_is_eligible_for_an_isolated_publisher(self):
  # Unit fixture: metadata shaped as a live record, without inference or a remote effect.
  digest=self.request['artifact_digest'];spec_digest='f'*64;frozen_digest='e'*64
  self.request.update(base='a'*40,frozen_digest=frozen_digest,spec_digest=spec_digest,acceptance_digest='d'*64,
                      reviewed_diff=sorted(self.request['files']),contract_digest=self.build['contract_digest'])
  self.receipt.update(simulated=False,author_model='glm-5.3-flash',base_sha='a'*40,
      artifact_digest=digest,allowed=sorted(self.request['files']),frozen_digest=frozen_digest,
      spec_digest=spec_digest,acceptance_digest='d'*64,contract_digest=self.build['contract_digest'])
  self.receipt['review']['content_digest']=digest
  self.receipt['circuit'].update(content_digest=digest,coverage={'complete':True},spec_digest=spec_digest,
                               acceptance_digest='d'*64)
  self.stage()
  self.assertIsNotNone(verified_receipt(self.store,self.request))
  for key,value in [('contract_digest','0'*64),('spec_digest','0'*64),('frozen_digest','0'*64),('attempt_generation',999),
                    ('base','b'*40),('build_id','other'),('artifact_digest','0'*64)]:
   with self.subTest(key=key):
    self.assertIsNone(verified_receipt(self.store,{**self.request,key:value}))
  self.store.cancel(self.build['build_id'])
  self.assertIsNone(verified_receipt(self.store,self.request))


if __name__=='__main__':unittest.main()
