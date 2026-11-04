"""Bootstrap authority never leaks into ordinary product publication or excerpt reviews."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.bootstrap import (BootstrapForge,EXTRA_PATHS,CI_DOC_PATHS,REPOSITORY,BASE_SHA,SOURCE_SHA,
    known_output_limit,known_unforwarded_second_review,known_second_output_limit,second_review_output_window,
    known_review_budget_stop,retain_closed_review,rearm_if_remote_absent)
from factory.store import Store
from factory.manifest import Catalog
from factory.github import GitHubForge,GitHubError
from factory.review import content_digest
from factory.flue_review import FlueReview


class BootstrapTests(unittest.TestCase):
    def test_rearming_a_permission_denial_reads_main_branch_and_pr_before_any_retry(self):
        class Forge:
            def __init__(self,mode):self.mode=mode;self.methods=[]
            def base_sha(self):return 'f'*40 if self.mode=='stale' else BASE_SHA
            def _ref(self,branch):return '/synthetic/'+branch
            def _request(self,method,path):
                self.methods.append(method)
                return (200 if self.mode=='branch' else 404),{}
            def find_pull_request(self,branch):return {'number':1} if self.mode=='pr' else None
        for mode in ('stale','branch','pr','absent'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root=Path(folder)/'state';request=self.retention_state(root,False)
                store=Store(root/'factory.db');build=store.by_attempt(request['attempt_id'])
                self.assertTrue(store.stage_publication(build,request,{}))
                job=store.claim_publication()
                store.finish_publication(job,{'status':'held','reason':'tree_create_failed:403'})
                forge=Forge(mode);result=rearm_if_remote_absent(store,request,forge)
                self.assertEqual(result['status'],'rearmed' if mode=='absent' else 'held')
                self.assertTrue(all(method=='GET' for method in forge.methods))
                self.assertEqual(store.by_attempt(request['attempt_id'])['status'],'gated' if mode=='absent' else 'held')

    def test_budget_repair_requires_settled_history_room_for_a_full_request_and_no_prior_repair(self):
        proof={'votes':[{'model':'glm-5.3-flash','verdict':'approve','execution':{
            'usage':{'complete':True,'cost_usd':'0.02'}}},
            {'model':'deepseek-4.1-flash','verdict':'error','execution':{'failure':'BUDGET_STOP',
                'forwarded_count':4,'usage':{'complete':True,'cost_usd':'0.045','estimated_cost_usd':'0.075'}}}],
            'attempts':[{'resumed_second_output_limit':True}]}
        self.assertTrue(known_review_budget_stop(proof))
        for mutate in (
            lambda p:p['votes'][1]['execution']['usage'].update(cost_usd='0.95'),
            lambda p:p['votes'][1]['execution']['usage'].update(complete=False),
            lambda p:p['votes'][1].update(verdict='reject'),
            lambda p:p['attempts'].append({'resumed_budget_settlement':True}),
            lambda p:p['attempts'].append({'execution':{'usage':{'complete':False}}}),
        ):
            changed=copy.deepcopy(proof);mutate(changed)
            self.assertFalse(known_review_budget_stop(changed))

    def test_a_second_review_output_limit_retries_once_only_with_final_known_usage(self):
        proof={'votes':[{'model':'glm-5.3-flash','verdict':'approve','execution':{
            'forwarded_count':4,'usage':{'complete':True,'cost_usd':'0.02'}}},
            {'model':'deepseek-4.1-flash','verdict':'error','execution':{'failure':'OUTPUT_LIMIT',
                'finish_reason':'length','forwarded_count':1,'usage':{
                    'complete':True,'output_tokens':16384,'cost_usd':'0.0195'}}}]}
        self.assertTrue(known_second_output_limit(proof))
        self.assertEqual(second_review_output_window(proof),16384)
        enlarged=copy.deepcopy(proof)
        enlarged['votes'][1]['execution']['reasoning_effort']='low'
        enlarged['attempts']=[{'resumed_second_output_limit':True}]
        self.assertEqual(second_review_output_window(enlarged),32768)
        enlarged['attempts'].append({'resumed_second_output_limit':True})
        self.assertIsNone(second_review_output_window(enlarged))
        for mutate in (
            lambda p:p['votes'][1].update(verdict='reject'),
            lambda p:p['votes'][1]['execution'].update(finish_reason='error'),
            lambda p:p['votes'][1]['execution']['usage'].update(complete=False),
            lambda p:p['votes'][1]['execution']['usage'].update(cost_usd=None),
            lambda p:p.update(attempts=[{'resumed_second_output_limit':True}]),
        ):
            changed=copy.deepcopy(proof);mutate(changed)
            self.assertFalse(known_second_output_limit(changed))

    def retention_state(self,root,expired):
        root.mkdir()
        request=self.request()
        catalog=Catalog({'schema_version':2,'count':1,'features':[dict(id='bootstrap',title='Bootstrap',
            area='foundation',size='L',phase='P0',tier=3,parallel=False,write_paths=['demo/forum-app/'],
            depends_on=[],file='bootstrap.md')]})
        store=Store(root/'factory.db');store.admit(['bootstrap'],'frozen',catalog)
        row=store.claim_next(catalog,lease_ns=0 if expired else 3600*10**9)
        request.update(attempt_id=row['attempt_id'],build_id=row['build_id'],
            attempt_generation=row['attempt_generation'],base=BASE_SHA,source_sha=SOURCE_SHA)
        (root/'request.json').write_text(json.dumps(request))
        return request

    def test_expired_known_closed_reviews_retain_bytes_and_votes_without_extending_old_lease(self):
        with tempfile.TemporaryDirectory() as folder:
            source,dest=Path(folder)/'old',Path(folder)/'fresh'
            prior=self.retention_state(source,True);current=self.retention_state(dest,False)
            proof={'artifact_digest':prior['artifact_digest'],'coverage':{'files':sorted(prior['files'])},
                'votes':[{'model':'glm-5.3-flash','verdict':'approve','execution':{'forwarded_count':2,
                    'usage':{'complete':True,'cost_usd':'0.02'}}},
                    {'verdict':'error','execution':{'failure':'AEION_HANDOVER','forwarded_count':0,
                    'usage':{'complete':True,'cost_usd':'0','basis':'proven_no_transport'}}}]}
            (source/'reviews.json').write_text(json.dumps(proof))
            self.assertEqual(retain_closed_review(source,dest)['status'],'retained')
            retained=json.loads((dest/'reviews.json').read_text())
            self.assertEqual(retained['votes'],proof['votes'])
            self.assertEqual(retained['retained_from_attempt'],prior['attempt_id'])
            self.assertEqual(Store(source/'factory.db').by_attempt(prior['attempt_id'])['status'],'cancelled')
            self.assertTrue(Store(dest/'factory.db').attempt_authorized(current['attempt_id'],0))

    def test_retention_cannot_release_an_unreconciled_prior_cost(self):
        with tempfile.TemporaryDirectory() as folder:
            source,dest=Path(folder)/'old',Path(folder)/'fresh'
            prior=self.retention_state(source,True);self.retention_state(dest,False)
            proof={'artifact_digest':prior['artifact_digest'],'coverage':{'files':sorted(prior['files'])},
                'attempts':[{'execution':{'usage':{'complete':False,'cost_usd':None}}}],
                'votes':[{'model':'glm-5.3-flash','verdict':'approve','execution':{'forwarded_count':2,
                    'usage':{'complete':True,'cost_usd':'0.02'}}},
                    {'verdict':'error','execution':{'failure':'AEION_HANDOVER','forwarded_count':0,
                    'usage':{'complete':True,'cost_usd':'0','basis':'proven_no_transport'}}}]}
            (source/'reviews.json').write_text(json.dumps(proof))
            with self.assertRaisesRegex(ValueError,'cost_unreconciled'):retain_closed_review(source,dest)
            self.assertFalse((dest/'reviews.json').exists())
            self.assertEqual(Store(source/'factory.db').by_attempt(prior['attempt_id'])['status'],'held')

    def test_only_an_unforwarded_second_review_preserves_the_exact_first_approval(self):
        proof={'votes':[{'model':'glm-5.3-flash','verdict':'approve','execution':{
            'forwarded_count':4,'usage':{'complete':True,'cost_usd':'0.02'}}},
            {'model':'qwen-3.8-flash','verdict':'error','execution':{'failure':'CONTEXT_UNKNOWN',
                'forwarded_count':0,'usage':{'complete':True,'basis':'proven_no_transport','cost_usd':'0'}}}]}
        self.assertTrue(known_unforwarded_second_review(proof))
        for mutate in (
            lambda p:p['votes'][1]['execution'].update(forwarded_count=1),
            lambda p:p['votes'][1].update(verdict='reject'),
            lambda p:p['votes'][0].update(verdict='reject'),
            lambda p:p['votes'][1]['execution']['usage'].update(complete=False),
            lambda p:p.update(attempts=[{'resumed_unforwarded':True}]),
        ):
            changed=copy.deepcopy(proof);mutate(changed)
            self.assertFalse(known_unforwarded_second_review(changed))

    def test_only_a_known_cost_closed_output_limit_can_resume_once(self):
        proof={'votes':[{'verdict':'error','execution':{'failure':'CLI_FAILED','forwarded_count':1,
            'usage':{'complete':True,'output_tokens':4096,'cost_usd':'0.01'}}}]}
        self.assertTrue(known_output_limit(proof))
        missing=copy.deepcopy(proof);missing['votes'][0]['execution']['usage']['complete']=False
        self.assertFalse(known_output_limit(missing))
        proof['attempts']=[{'prior':'retained'}]
        self.assertFalse(known_output_limit(proof))

    def test_direct_bootstrap_entrypoint_preserves_standard_library_queue(self):
        demo=Path(__file__).resolve().parents[1]
        code=('import runpy,sys; sys.path[:0]='+repr([str(demo/'factory'),str(demo)])
              +'; runpy.run_path('+repr(str(demo/'factory/bootstrap.py'))
              +',run_name="bootstrap_import_test"); import queue; assert hasattr(queue,"LifoQueue")')
        result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def request(self):
        files={'demo/forum-app/Hello.java':'class Hello {}\n',**{p:'Trusted '+p+'\n' for p in EXTRA_PATHS}}
        return {'files':files,'artifact_digest':content_digest(files)}

    def test_normal_forge_still_refuses_the_supervisor_ci_bundle(self):
        with self.assertRaisesRegex(GitHubError,'forbidden_product_content'):
            GitHubForge(REPOSITORY)._files(self.request())

    def test_bootstrap_accepts_only_its_complete_exact_frozen_bundle(self):
        request=self.request();forge=BootstrapForge(request,REPOSITORY)
        self.assertEqual(forge._files(request),request['files'])
        for path in ('.github/workflows/ci.yml','demo/forum-app/Hello.java'):
            changed=copy.deepcopy(request);changed['files'][path]='Different bytes'
            changed['artifact_digest']=content_digest(changed['files'])
            with self.subTest(path=path),self.assertRaisesRegex(GitHubError,'bootstrap_content_changed'):
                forge._files(changed)

    def test_bootstrap_cannot_add_another_policy_file(self):
        request=self.request();request['files']['.github/workflows/other.yml']='Injected policy'
        request['artifact_digest']=content_digest(request['files'])
        with self.assertRaisesRegex(ValueError,'bootstrap_extra_paths'):
            BootstrapForge(request,REPOSITORY)

    def test_ci_documentation_fix_is_exact_and_legacy_frozen_bundles_remain_readable(self):
        legacy=self.request()
        self.assertEqual(BootstrapForge(legacy,REPOSITORY)._files(legacy),legacy['files'])
        current=copy.deepcopy(legacy)
        current['files'].update({p:'Updated CI documentation\n' for p in CI_DOC_PATHS})
        current['artifact_digest']=content_digest(current['files'])
        self.assertEqual(BootstrapForge(current,REPOSITORY)._files(current),current['files'])
        del current['files'][next(iter(CI_DOC_PATHS))]
        current['artifact_digest']=content_digest(current['files'])
        with self.assertRaisesRegex(ValueError,'bootstrap_extra_paths'):
            BootstrapForge(current,REPOSITORY)

    def test_large_complete_review_is_supervisor_bounded_and_never_silently_truncated(self):
        with self.assertRaisesRegex(ValueError,'REVIEW_BOUNDS_INVALID'):
            FlueReview(max_prompt_bytes=240001)
        with self.assertRaisesRegex(ValueError,'REVIEW_BOUNDS_INVALID'):
            FlueReview(cost_limit='1.01')
        with self.assertRaisesRegex(ValueError,'REVIEW_BOUNDS_INVALID'):
            FlueReview(deepseek_effort='off')
        for cost in ('NaN','Infinity','invalid'):
            with self.subTest(cost=cost),self.assertRaisesRegex(ValueError,'REVIEW_BOUNDS_INVALID'):
                FlueReview(cost_limit=cost)
        role=FlueReview(max_prompt_bytes=200000,cost_limit='0.25')
        with patch('factory.flue_review.FactorySession') as session:
            with self.assertRaisesRegex(ValueError,'REVIEW_NOT_ADMITTED'):
                role('glm-5.3-flash','é'*100001)
            session.assert_not_called()
        self.assertEqual(role.last_usage['basis'],'proven_no_transport')


if __name__=='__main__':unittest.main()
