"""Atomic Git publication and exact-head protected merge at the HTTP boundary."""
import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.github import GitHubForge,GitHubError,branch_name
from factory.review import content_digest

BASE='a'*40; HEAD='b'*40; TREE='c'*40; MERGE='d'*40
FILES={'demo/forum-docs/example.md':'Reviewed feature\n'}
ATTEMPT='1'*32


def request():
 return {'attempt_id':ATTEMPT,'feature_id':'082','title':'Synthetic feature','base':BASE,
         'artifact_digest':content_digest(FILES),'files':dict(FILES)}


class Transport:
 def __init__(self):
  self.calls=[];self.main=BASE;self.branch=None;self.pr=None;self.check='success';self.app=15368
  self.output=None
  self.strict=True;self.protection_http=200;self.diff_files=FILES.copy()
 def __call__(self,method,url,payload,headers):
  self.calls.append((method,url,payload))
  path=url.split('/repos/o/r',1)[-1]
  if method=='GET' and path=='/git/ref/heads/main':return 200,{'object':{'sha':self.main}}
  if method=='GET' and path.startswith('/git/ref/heads/aeion/build-'):
   return (200,{'object':{'sha':self.branch}}) if self.branch else (404,{})
  if method=='GET' and path.startswith('/git/commits/'):
   return 200,{'sha':path.rsplit('/',1)[-1],'tree':{'sha':TREE},'parents':[{'sha':BASE}]}
  if method=='POST' and path=='/git/trees':return 201,{'sha':TREE}
  if method=='POST' and path=='/git/commits':return 201,{'sha':HEAD}
  if method=='POST' and path=='/git/refs':self.branch=payload['sha'];return 201,{'object':{'sha':self.branch}}
  if method=='GET' and path.startswith('/pulls?'):return 200,[self.pr] if self.pr else []
  if method=='POST' and path=='/pulls':
   self.pr={'number':7,'html_url':'https://github.com/o/r/pull/7','state':'open','merged':False,
    'mergeable':True,'mergeable_state':'clean','base':{'sha':BASE,'ref':'main','repo':{'full_name':'o/r'}},
    'head':{'sha':self.branch,'ref':branch_name(ATTEMPT),'repo':{'full_name':'o/r'}}}
   return 201,self.pr
  if method=='GET' and path=='/pulls/7':return 200,self.pr
  if method=='GET' and '/compare/' in path:
   if path.endswith(MERGE+'...'+MERGE):return 200,{'status':'identical','ahead_by':0}
   return 200,{'files':[{'filename':p,'status':'added','sha':hashlib.sha1(b'blob '+str(len(t.encode())).encode()+b'\0'+t.encode()).hexdigest()} for p,t in self.diff_files.items()]}
  if method=='GET' and path.startswith('/git/trees/'):
   return 200,{'truncated':False,'tree':[{'path':p,'mode':'100644','type':'blob','sha':hashlib.sha1(b'blob '+str(len(t.encode())).encode()+b'\0'+t.encode()).hexdigest()} for p,t in self.diff_files.items()]}
  if method=='GET' and path=='/branches/main/protection':
   return self.protection_http,{'required_status_checks':{'strict':self.strict,'checks':[{'context':'Product artifacts','app_id':15368}]},
     'enforce_admins':{'enabled':True},'allow_force_pushes':{'enabled':False},'allow_deletions':{'enabled':False}}
  if method=='GET' and '/check-runs' in path:
   run={'head_sha':HEAD,'name':'Product artifacts','status':'completed','conclusion':self.check,'app':{'id':self.app}}
   if self.output:run['output']=self.output
   return 200,{'total_count':1,'check_runs':[run]}
  if method=='PUT' and path=='/pulls/7/merge':
   assert payload['sha']==HEAD
   self.main=MERGE;self.pr={**self.pr,'state':'closed','merged':True,'merge_commit_sha':MERGE}
   return 200,{'merged':True,'sha':MERGE}
  raise AssertionError((method,path))
 def writes(self):return [x for x in self.calls if x[0]!='GET']


class AtomicForgeTests(unittest.TestCase):
 def setUp(self):
  self.transport=Transport()
  self.forge=GitHubForge('o/r',token='synthetic',transport=self.transport,dry_run=False,allow_merge=True)

 def publish(self):return self.forge.publish(request())

 def test_stale_base_stops_before_any_write(self):
  self.transport.main='e'*40
  with self.assertRaisesRegex(GitHubError,'stale_base'):self.publish()
  self.assertEqual(self.transport.writes(),[])

 def test_publication_response_never_echoes_the_role_credential(self):
  self.assertNotIn('synthetic',repr(self.publish()))

 def test_one_tree_commit_instead_of_per_file_updates_and_replay_is_read_only(self):
  first=self.publish();writes=len(self.transport.writes())
  second=self.publish()
  self.assertEqual(first['pr']['head_sha'],HEAD)
  self.assertEqual(second['pr']['head_sha'],HEAD)
  self.assertEqual(len(self.transport.writes()),writes)
  self.assertFalse(any('/contents/' in call[1] for call in self.transport.calls))
  trees=[x[2] for x in self.transport.calls if x[0]=='POST' and x[1].endswith('/git/trees')]
  self.assertEqual(len(trees),1);self.assertEqual(trees[0]['base_tree'],TREE)

 def test_existing_branch_with_an_extra_unreviewed_file_is_refused(self):
  self.publish();self.transport.diff_files['.github/workflows/evil.yml']='changed'
  with self.assertRaisesRegex(GitHubError,'branch_content_mismatch'):self.publish()

 def test_publish_never_merges_even_with_request_flag(self):
  req=request();req['merge']=True
  with self.assertRaisesRegex(GitHubError,'release_role'):self.forge.publish(req)
  self.assertEqual(self.transport.writes(),[])

 def test_exact_head_green_ci_merge_confirms_result_on_main(self):
  self.publish()
  result=self.forge.merge(7,expected_head=HEAD,expected_base=BASE)
  self.assertEqual(result['status'],'merged');self.assertEqual(result['merge_sha'],MERGE)
  self.assertEqual(result['main_sha'],MERGE)

 def test_a_failed_required_check_names_itself_and_drops_its_log(self):
  self.publish()
  self.transport.check='failure'
  self.transport.output={'summary':'leaked ghp_'+'a'*36}
  result=self.forge.merge(7,expected_head=HEAD,expected_base=BASE)
  self.assertEqual(result['status'],'held')
  self.assertEqual(result['failed_checks'],[{'name':'Product artifacts','conclusion':'failure'}])
  self.assertNotIn('ghp_',repr(result))
  self.assertFalse(any(x[0]=='PUT' for x in self.transport.calls))
  named=GitHubForge._failed_checks(['bad\nname','CI / build'],{
      'bad\nname':{'conclusion':'failure'},'CI / build':{'conclusion':'timed_out'},
      'skipped-not-required':{'conclusion':'success'}})
  self.assertEqual(named,[{'name':'check','conclusion':'failure'},{'name':'CI / build','conclusion':'timed_out'}])

 def test_failed_or_forged_ci_and_non_strict_protection_never_merge(self):
  for key,value in [('check','failure'),('app',1),('strict',False),('protection_http',403)]:
   with self.subTest(key=key):
    self.setUp();self.publish();setattr(self.transport,key,value)
    result=self.forge.merge(7,expected_head=HEAD,expected_base=BASE)
    self.assertNotEqual(result['status'],'merged')
    self.assertFalse(any(x[0]=='PUT' for x in self.transport.calls))

 def test_changed_head_or_base_never_merges(self):
  for field in ['head','base']:
   with self.subTest(field=field):
    self.setUp();self.publish();self.transport.pr[field]['sha']='e'*40
    result=self.forge.merge(7,expected_head=HEAD,expected_base=BASE)
    self.assertNotEqual(result['status'],'merged')
    self.assertFalse(any(x[0]=='PUT' for x in self.transport.calls))


if __name__=='__main__':unittest.main()
