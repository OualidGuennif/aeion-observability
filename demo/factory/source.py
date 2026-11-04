"""Synchronize protected product main through one isolated read-key process.

Spec: knowledge/components/factory-flue.md
"""
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[2]
SOURCE_URL='https://github.com/OualidGuennif/aeion-autonomous-forum.git'
MAIN_REF='refs/remotes/origin/main'
SHA=re.compile('[a-f0-9]{40}')


class SourceSyncError(ValueError):
    """Fixed operational codes only; raw Git diagnostics never leave this role."""


def fetch_main(source,token,*,run=subprocess.run):
    source=Path(source)
    if source.is_symlink() or (source/'.git').is_symlink() or not (source/'.git').is_dir():
        raise SourceSyncError('source_checkout_unavailable')
    if not isinstance(token,str) or not token:
        raise SourceSyncError('source_credential_unavailable')
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/nonexistent','LANG':'C.UTF-8',
         'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0'}
    git=['git','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-c','gc.auto=0',
         '-c','maintenance.auto=false','-c','credential.helper=','-c','http.followRedirects=false',
         '-c','http.sslVerify=true',
         '-C',str(source.resolve())]
    def invoke(*args,auth=False):
        private_env=dict(env)
        if auth:
            private_env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
                GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+token).encode()).decode())
        try:return run(git+list(args),env=private_env,capture_output=True,text=True,timeout=90)
        except (OSError,subprocess.TimeoutExpired):raise SourceSyncError('source_fetch_failed') from None
    def revision(ref):
        result=invoke('rev-parse','--verify',ref+'^{commit}')
        return result.stdout.strip() if result.returncode==0 and SHA.fullmatch(result.stdout.strip()) else None
    old=revision(MAIN_REF)
    temporary='refs/aeion/source-sync/'+uuid.uuid4().hex
    try:
        result=invoke('fetch','--no-tags','--no-recurse-submodules','--no-write-fetch-head',
                      SOURCE_URL,'refs/heads/main:'+temporary,auth=True)
        if result.returncode:raise SourceSyncError('source_fetch_failed')
        new=revision(temporary)
        if new is None:raise SourceSyncError('source_fetch_failed')
        if old and invoke('merge-base','--is-ancestor',old,new).returncode:
            raise SourceSyncError('source_main_rewritten')
        if invoke('update-ref',MAIN_REF,new,old or '0'*40).returncode:
            raise SourceSyncError('source_ref_changed')
        return new
    finally:
        fetched=revision(temporary)
        if fetched:invoke('update-ref','-d',temporary,fetched)


class SourceSynchronizer:
    def __init__(self,root,*,run=subprocess.run):
        self.root,self.run=Path(root).resolve(),run

    def __call__(self):
        env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':'/nonexistent',
             'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
        try:
            result=self.run([sys.executable,str(self.root/'demo/factory/source.py')],env=env,
                            capture_output=True,text=True,timeout=120)
            if result.returncode or len(result.stdout.encode())>1024:raise ValueError
            body=json.loads(result.stdout)
            if body.get('status')=='synced' and isinstance(body.get('main_sha'),str) and SHA.fullmatch(body['main_sha']):
                return body['main_sha']
            if body.get('reason') in {'source_checkout_unavailable','source_credential_unavailable',
                    'source_fetch_failed','source_main_rewritten','source_ref_changed'}:
                raise SourceSyncError(body['reason'])
        except (OSError,ValueError,AttributeError,subprocess.TimeoutExpired) as error:
            if isinstance(error,SourceSyncError):raise
        raise SourceSyncError('source_sync_unavailable')


def main():
    # Direct execution must not let factory/queue.py shadow the standard library.
    here=Path(__file__).resolve().parent
    sys.path[:]=[p for p in sys.path if Path(p or '.').resolve()!=here]
    sys.path.insert(0,str(ROOT/'demo'))
    from factory.keys import assert_only,for_role,names_for,CredentialError
    from factory.gh_probe import load_secret
    try:
        assert_only('build');load_secret(names_for('build')[0]);assert_only('build')
        _,token=for_role('build')
        sha=fetch_main(ROOT/'demo/.local/factory/agents/aeion-autonomous-forum',token)
        result={'status':'synced','main_sha':sha}
    except CredentialError:result={'status':'held','reason':'source_credential_unavailable'}
    except SourceSyncError as error:result={'status':'held','reason':str(error)}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
