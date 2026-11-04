"""Read-role source synchronization updates only origin/main and preserves operator work."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.source import SourceSynchronizer,SourceSyncError,fetch_main,SOURCE_URL


class SourceSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.remote=self.root/'remote.git';self.seed=self.root/'seed'
        self.source=self.root/'checkout';self.environ={'PATH':os.environ.get('PATH','/usr/bin:/bin'),
            'HOME':'/nonexistent','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
        self.git('init','-q','--bare',str(self.remote));self.git('init','-q',str(self.seed))
        self.git('-C',str(self.seed),'config','user.name','Fixture')
        self.git('-C',str(self.seed),'config','user.email','fixture@example.invalid')
        (self.seed/'source.txt').write_text('baseline\n')
        self.git('-C',str(self.seed),'add','.');self.git('-C',str(self.seed),'commit','-qm','baseline')
        self.git('-C',str(self.seed),'branch','-M','main')
        self.git('-C',str(self.seed),'push','-q',str(self.remote),'main')
        self.git('clone','-q','-b','main',str(self.remote),str(self.source))
        self.old=self.git('-C',str(self.source),'rev-parse','HEAD').stdout.strip()
        (self.seed/'source.txt').write_text('new main\n')
        self.git('-C',str(self.seed),'commit','-qam','new main')
        self.git('-C',str(self.seed),'push','-q',str(self.remote),'main')
        self.new=self.git('-C',str(self.seed),'rev-parse','HEAD').stdout.strip()
        (self.source/'source.txt').write_text('operator draft\n')
        (self.source/'untracked.txt').write_text('keep this\n')

    def git(self,*args):
        return subprocess.run(['git','-c','core.hooksPath=/dev/null','-c','gc.auto=0',*args],
            capture_output=True,text=True,check=True,env=self.environ)

    def transport(self,argv,**kwargs):
        self.assertNotIn('synthetic-build-key',str(argv))
        for key in ('OPENCODE_API_KEY','GH_BUILD_KEY','GH_API_KEY','GH_RELEASE_KEY','GH_TOKEN','GITHUB_TOKEN'):
            self.assertNotIn(key,kwargs['env'])
        argv=list(argv)
        if 'fetch' in argv:
            self.assertIn('--no-write-fetch-head',argv)
            argv[argv.index(SOURCE_URL)]=str(self.remote)
        return subprocess.run(argv,**kwargs)

    def assert_preserved(self):
        self.assertEqual(self.git('-C',str(self.source),'rev-parse','HEAD').stdout.strip(),self.old)
        self.assertEqual((self.source/'source.txt').read_text(),'operator draft\n')
        self.assertEqual((self.source/'untracked.txt').read_text(),'keep this\n')
        self.assertEqual(self.git('-C',str(self.source),'for-each-ref','refs/aeion/source-sync/').stdout,'')

    def test_new_main_is_fetched_idempotently_without_checkout_or_ambient_credentials(self):
        for _ in range(2):
            self.assertEqual(fetch_main(self.source,'synthetic-build-key',run=self.transport),self.new)
        self.assertEqual(self.git('-C',str(self.source),'rev-parse','refs/remotes/origin/main').stdout.strip(),self.new)
        self.assert_preserved()

    def test_fetch_failure_keeps_the_previous_ref_and_never_exposes_remote_diagnostics(self):
        def fail(argv,**kwargs):
            if 'fetch' in argv:return subprocess.CompletedProcess(argv,1,'','PRIVATE_CANARY')
            return self.transport(argv,**kwargs)
        with self.assertRaisesRegex(SourceSyncError,'^source_fetch_failed$'):
            fetch_main(self.source,'synthetic-build-key',run=fail)
        self.assertEqual(self.git('-C',str(self.source),'rev-parse','refs/remotes/origin/main').stdout.strip(),self.old)
        self.assert_preserved()

    def test_rewritten_remote_main_does_not_replace_the_last_accepted_main(self):
        fetch_main(self.source,'synthetic-build-key',run=self.transport)
        self.git('--git-dir',str(self.remote),'update-ref','refs/heads/main',self.old,self.new)
        with self.assertRaisesRegex(SourceSyncError,'^source_main_rewritten$'):
            fetch_main(self.source,'synthetic-build-key',run=self.transport)
        self.assertEqual(self.git('-C',str(self.source),'rev-parse','refs/remotes/origin/main').stdout.strip(),self.new)
        self.assert_preserved()

    def test_concurrent_ref_change_is_not_overwritten(self):
        def race(argv,**kwargs):
            if 'update-ref' in argv and 'refs/remotes/origin/main' in argv:
                self.git('-C',str(self.source),'update-ref','refs/remotes/origin/main',self.new,self.old)
            return self.transport(argv,**kwargs)
        with self.assertRaisesRegex(SourceSyncError,'^source_ref_changed$'):
            fetch_main(self.source,'synthetic-build-key',run=race)
        self.assertEqual(self.git('-C',str(self.source),'rev-parse','refs/remotes/origin/main').stdout.strip(),self.new)
        self.assert_preserved()

    def test_role_subprocess_does_not_inherit_the_parent_keys_and_validates_its_reply(self):
        def role(argv,**kwargs):
            self.assertEqual(set(kwargs['env']),{'PATH','HOME','LANG','PYTHONDONTWRITEBYTECODE'})
            return subprocess.CompletedProcess(argv,0,json.dumps({'status':'synced','main_sha':self.new}), '')
        with patch.dict(os.environ,{'GH_API_KEY':'synthetic','GH_RELEASE_KEY':'synthetic','OPENCODE_API_KEY':'synthetic'}):
            self.assertEqual(SourceSynchronizer(self.root,run=role)(),self.new)
        def invalid(argv,**kwargs):return subprocess.CompletedProcess(argv,0,'{"status":"synced","main_sha":"untrusted"}','')
        with self.assertRaisesRegex(SourceSyncError,'^source_sync_unavailable$'):
            SourceSynchronizer(self.root,run=invalid)()


if __name__=='__main__':unittest.main()
