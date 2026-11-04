"""Real isolated role subprocesses and loopback HTTP, entirely synthetic forge/receipts.

No owner environment, credential loader, GitHub request, model call or real merge is used.
The test-only wrapper injects fake role keys and transport; production has no such endpoint flag.
"""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.publication import PublicationCoordinator, RoleExecutor, REPOSITORY
from factory.review import content_digest
from factory.store import Store
from test_factory_github_atomic import Transport, BASE, HEAD, MERGE


class PublicationHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.state=self.root/'demo/.local/factory/test'
        self.store=Store(self.state/'factory.db')
        catalog=Catalog({'schema_version':2,'count':1,'features':[dict(id='082',title='Docs',area='corpus',
            size='S',phase='P0',parallel=False,tier=3,write_paths=['demo/forum-docs/'],depends_on=[],file='082.md')]})
        self.store.admit(['082'],'synthetic-http-fixture',catalog)
        self.build=self.store.claim_next(catalog)
        files={'demo/forum-docs/example.md':'Reviewed feature\n'};digest=content_digest(files)
        self.request=dict(attempt_id=self.build['attempt_id'],build_id=self.build['build_id'],
            attempt_generation=0,issuer='gate',feature_id='082',target_repo=REPOSITORY,
            base=BASE,head=BASE,files=files,artifact_digest=digest,reviewed_diff=sorted(files),
            write_scopes=['demo/forum-docs/'],review_status='approved',spec_digest='f'*64,
            acceptance_digest='d'*64,frozen_digest='e'*64,contract_digest=self.build['contract_digest'])
        receipt=dict(simulated=False,author_model='glm-5.3-flash',base_sha=BASE,artifact_digest=digest,
            allowed=sorted(files),spec_digest='f'*64,acceptance_digest='d'*64,frozen_digest='e'*64,
            contract_digest=self.build['contract_digest'],gate={'status':'passed'},
            review={'status':'approved','content_digest':digest},circuit={'status':'approved',
            'author_model':'glm-5.3-flash','content_digest':digest,'spec_digest':'f'*64,
            'acceptance_digest':'d'*64,'coverage':{'complete':True},'votes':[
                {'model':'qwen-3.8-flash','family':'qwen','verdict':'approve'},
                {'model':'claude-haiku-5.5','family':'anthropic','verdict':'approve'}]})
        self.coordinator=PublicationCoordinator(self.store)
        self.coordinator.stage(self.build,self.request,receipt)
        self.transport=Transport();self.pending=True;self.cancel_on_check=False;self.roles=[]
        self.drop_merge_response=False
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def handle_request(self):
                length=int(self.headers.get('Content-Length','0'))
                payload=json.loads(self.rfile.read(length)) if length else None
                owner.roles.append(self.headers.get('Authorization'))
                status,body=owner.transport(self.command,'https://api.github.com/repos/o/r'+self.path.split('/repos/'+REPOSITORY,1)[-1],payload,{})
                body=copy.deepcopy(body)
                if self.command=='PUT' and owner.drop_merge_response:
                    status,body=503,{}  # Remote effect happened; its success response was lost.
                if '/check-runs' in self.path:
                    if owner.pending:body['check_runs'][0]['status']='in_progress'
                    if owner.cancel_on_check:owner.store.cancel(owner.build['build_id'])
                text=json.dumps(body).replace('o/r',REPOSITORY)
                data=text.encode();self.send_response(status)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)))
                self.end_headers();self.wfile.write(data)
            do_GET=do_POST=do_PUT=handle_request
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.wrapper=self.root/'test_role.py'
        demo=Path(__file__).resolve().parents[1]
        self.wrapper.write_text('''import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,DEMO)
from factory import publication_role as role
from factory.github import GitHubForge,_urllib_transport,API
from factory.keys import names_for
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--fixture-root');parser.add_argument('--fixture-url')
fixture,remaining=parser.parse_known_args()
role.ROOT=Path(fixture.fixture_root)
selected=remaining[remaining.index('--role')+1]
def load(name):
 assert name==names_for(selected)[0]
 os.environ[name]='synthetic-'+selected
role.load_secret=load
def transport(method,url,payload,headers):
 assert url.startswith(API+'/repos/OualidGuennif/aeion-autonomous-forum/')
 return _urllib_transport(method,fixture.fixture_url+url[len(API):],payload,headers)
role.GitHubForge=lambda *a,**kw:GitHubForge(*a,**kw,transport=transport)
sys.argv=[sys.argv[0],*remaining]
raise SystemExit(role.main())
'''.replace('DEMO',repr(str(demo)),1))

    def step(self):
        job=self.store.claim_publication()
        self.assertIsNotNone(job)
        original_run=subprocess.run
        def start(argv,**kwargs):
            self.assertFalse(any(k in kwargs['env'] for k in ('GH_API_KEY','GH_RELEASE_KEY','OPENCODE_API_KEY')))
            return original_run([sys.executable,str(self.wrapper),*argv[2:],
                '--fixture-root',str(self.root),'--fixture-url',f'http://127.0.0.1:{self.server.server_port}'],**kwargs)
        with patch('factory.publication.subprocess.run',side_effect=start):
            result=RoleExecutor(self.state)(job)
        return self.store.finish_publication(job,result,simulated=False,delay_ns=0)

    def test_separate_publish_release_processes_wait_for_exact_ci_and_confirm_synthetic_main(self):
        self.assertEqual(self.step()['status'],'pr_open')
        self.assertEqual(set(self.roles),{'Bearer synthetic-publish'})
        self.store=Store(self.store.path)  # Resume from persisted outbox, no rebuilding.
        self.assertEqual(self.step()['status'],'pr_open')
        self.assertFalse(any(c[0]=='PUT' for c in self.transport.calls))
        self.pending=False
        self.assertEqual(self.step()['status'],'merged')
        self.assertEqual(self.transport.main,MERGE)
        receipt=json.loads(self.store.board()[0]['receipt'])
        self.assertEqual(receipt['publisher']['main_sha'],MERGE)
        self.assertTrue(receipt['publisher']['confirmed_main'])
        self.assertEqual(set(self.roles),{'Bearer synthetic-publish','Bearer synthetic-release'})

    def test_cancellation_after_green_ci_revokes_merge_before_http_effect(self):
        self.assertEqual(self.step()['status'],'pr_open')
        self.pending=False;self.cancel_on_check=True
        self.assertEqual(self.step()['status'],'cancelled')
        self.assertEqual(self.transport.main,BASE)
        self.assertFalse(any(c[0]=='PUT' for c in self.transport.calls))
        self.assertEqual(self.store.board()[0]['status'],'cancelled')

    def test_lost_merge_response_reconciles_by_readback_without_a_second_merge(self):
        self.assertEqual(self.step()['status'],'pr_open')
        self.pending=False;self.drop_merge_response=True
        self.assertEqual(self.step()['status'],'pr_open')
        self.assertEqual(self.transport.main,MERGE)
        self.assertEqual(self.step()['status'],'merged')
        self.assertEqual(sum(c[0]=='PUT' for c in self.transport.calls),1)


if __name__=='__main__':unittest.main()
