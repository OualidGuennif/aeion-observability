"""Host-side OpenShell qualification. No model call; no agent runs outside OpenShell."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import time
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from sandbox import BUNDLE_FILES

from openshell import SandboxClient, TlsConfig
from openshell._proto import openshell_pb2 as api, sandbox_pb2 as pb


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint',default='localhost:17670')
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--image',default='aeion-openshell-agent:local')
    args=parser.parse_args();root=args.state.resolve();tls=root/'tls'
    assert os.environ.get('OPENSHELL_TELEMETRY_ENABLED')=='false'
    client=SandboxClient(args.endpoint,tls=TlsConfig(ca_path=tls/'ca.crt',cert_path=tls/'client/tls.crt',key_path=tls/'client/tls.key'),timeout=120)
    folder=root/'qualification';folder.mkdir(mode=0o700,exist_ok=True)
    out=folder/'security.json';out.unlink(missing_ok=True)
    assert client.health().version=='0.1.5'
    name='ae-qualification';ref=None
    try:
        policy=pb.SandboxPolicy(version=1,
            filesystem=pb.FilesystemPolicy(include_workdir=True,read_only=['/bin','/usr','/lib','/etc','/proc','/opt/demo','/dev/urandom','/var/log'],read_write=['/tmp','/dev/null']),
            landlock=pb.LandlockPolicy(compatibility='hard_requirement'),
            process=pb.ProcessPolicy(run_as_user='10001',run_as_group='10001'))
        ref=client.create(workspace='default',name=name,spec=api.SandboxSpec(template=api.SandboxTemplate(image=args.image),policy=policy,command=['/bin/sleep','infinity']))
        client.wait_ready(name,workspace='default',timeout_seconds=120)
        probe='''import os,json,socket
checks={'uid':os.getuid()==10001}
try:
 open('/etc/aeion-forbidden','w').write('blocked')
 checks['filesystem_denied']=False
except PermissionError:checks['filesystem_denied']=True
try:
 s=socket.create_connection(('example.com',443),timeout=3);s.close();checks['network_denied']=False
except OSError:checks['network_denied']=True
print(json.dumps(checks))'''
        result=client.exec(name,['python3','-c',probe],workspace='default',no_login_shell=True,timeout_seconds=15)
        evidence=json.loads(result.stdout)
        assert result.exit_code==0 and evidence=={'uid':True,'filesystem_denied':True,'network_denied':True},evidence
        script='import hashlib,json,pathlib; paths='+repr(BUNDLE_FILES)+'; print(json.dumps({name:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() for name,path in paths.items()}))'
        bundle=client.exec(name,['python3','-c',script],workspace='default',no_login_shell=True,timeout_seconds=15)
        assert bundle.exit_code==0
        evidence['bundle_sha256']=json.loads(bundle.stdout)
        names=subprocess.check_output([shutil.which('docker'),'ps','--format','{{.Names}}'],close_fds=False).decode().splitlines()
        supervisor=next(n for n in names if ref.id in n and n.endswith('-supervisor'))
        inspected=json.loads(subprocess.check_output([shutil.which('docker'),'inspect',supervisor],close_fds=False))[0]
        values=dict(v.split('=',1) for v in inspected['Config']['Env'] if '=' in v)
        assert values.get('OPENSHELL_TELEMETRY_ENABLED')=='false'
        workload=next(n for n in names if ref.id in n and not n.endswith('-supervisor'))
        config=json.loads(subprocess.check_output([shutil.which('docker'),'inspect',workload],close_fds=False))[0]
        assert config['HostConfig']['NetworkMode']=='none'
        assert not any(m['Source'].endswith('docker.sock') for m in config['Mounts'])
        evidence.update(version='0.1.5',telemetry_disabled=True,network_mode='none',sandbox_id=ref.id,
            agent_image=args.image,ca_sha256=hashlib.sha256((tls/'ca.crt').read_bytes()).hexdigest(),
            qualified_ns=time.time_ns(),expires_ns=time.time_ns()+86400000000000)
    finally:
        if ref:
            deletion=client.delete(name,workspace='default');client.wait_deleted(name,workspace='default',expected_sandbox_id=deletion.sandbox_id,timeout_seconds=120)
        client.close()
    # Publish readiness only after the probe workload has been confirmed deleted.
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(evidence,indent=2));tmp.chmod(0o600);tmp.replace(out)
    print(json.dumps(evidence))


if __name__=='__main__':main()
