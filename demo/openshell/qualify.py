"""Host-side OpenShell qualification. No model call; no agent runs outside OpenShell."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import time
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from grpc_fork import disable_grpc_fork_handlers
disable_grpc_fork_handlers()  # before the OpenShell client imports gRPC
from sandbox import BUNDLE_FILES, COLLECT_SCRIPT, MAX_SYNC_BYTES, SANDBOX_OUT, materialize

from openshell import SandboxClient, TlsConfig
from openshell._proto import openshell_pb2 as api, sandbox_pb2 as pb
from google.protobuf.json_format import ParseDict


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint',default='localhost:17670')
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--image',default='aeion-openshell-agent:local')
    parser.add_argument('--uid',type=int,default=10001)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--volume',default='aeion-openshell-work')
    args=parser.parse_args();root=args.state.resolve();tls=root/'tls'
    assert os.environ.get('OPENSHELL_TELEMETRY_ENABLED')=='false'
    client=SandboxClient(args.endpoint,tls=TlsConfig(ca_path=tls/'ca.crt',cert_path=tls/'client/tls.crt',key_path=tls/'client/tls.key'),timeout=120)
    folder=root/'qualification';folder.mkdir(mode=0o700,exist_ok=True)
    out=folder/'security.json';out.unlink(missing_ok=True)
    assert client.health().version=='0.1.7' and args.uid>0
    name='ae-qualification';ref=None
    # A run-shaped folder inside the work volume: only `run/` is mounted; `outside/` must stay invisible.
    work=args.work.resolve();probe_root=Path(tempfile.mkdtemp(prefix='.bind-probe-',dir=work));run=probe_root/'run'
    (run/'workspace/src').mkdir(parents=True);(probe_root/'outside').mkdir();(probe_root/'outside/secret.txt').write_text('host-only')
    if args.uid!=os.getuid():
        run.chmod(0o711);(run/'workspace').chmod(0o755);(run/'workspace/src').chmod(0o777)
    try:
        policy=pb.SandboxPolicy(version=1,
            filesystem=pb.FilesystemPolicy(include_workdir=False,read_only=['/bin','/usr','/lib','/etc','/proc','/opt/demo','/dev/urandom','/var/log','/sandbox'],read_write=['/tmp','/dev/null']),
            landlock=pb.LandlockPolicy(compatibility='hard_requirement'),
            process=pb.ProcessPolicy(run_as_user=str(args.uid),run_as_group=str(args.uid)))
        spec=api.SandboxSpec(template=api.SandboxTemplate(image=args.image),policy=policy,command=['/bin/sleep','infinity'])
        ref=client.create(workspace='default',name=name,spec=spec)
        client.wait_ready(name,workspace='default',timeout_seconds=120)
        probe='''import json,os,socket,sys
out,watch,uid=sys.argv[1],sys.argv[2],int(sys.argv[3])
checks={'uid':os.getuid()==uid}
try:
 open('/etc/aeion-forbidden','w').write('blocked')
 checks['filesystem_denied']=False
except PermissionError:checks['filesystem_denied']=True
os.makedirs(out+'/workspace/src',exist_ok=True)
open(out+'/workspace/src/agent.txt','w').write('from-sandbox')
checks['sandbox_write']=open(out+'/workspace/src/agent.txt').read()=='from-sandbox'
try:
 open(watch+'/workspace/HANDOVER.md','w').write('forged')
 checks['workspace_read_only']=False
except (PermissionError,OSError):checks['workspace_read_only']=True
checks['host_outside_invisible']=not os.path.exists(os.path.dirname(watch)+'/outside/secret.txt')
try:
 s=socket.create_connection(('example.com',443),timeout=3);s.close();checks['network_denied']=False
except OSError:checks['network_denied']=True
print(json.dumps(checks))'''
        result=client.exec(name,['python3','-c',probe,SANDBOX_OUT,str(run),str(args.uid)],workspace='default',no_login_shell=True,timeout_seconds=15)
        evidence=json.loads(result.stdout)
        assert result.exit_code==0 and evidence=={'uid':True,'filesystem_denied':True,'sandbox_write':True,
            'workspace_read_only':True,'host_outside_invisible':True,'network_denied':True},evidence
        # Copy-out transport: results leave the sandbox over the exec channel, never through a
        # host-backed write (which lands but returns EACCES on Docker Desktop).
        collected=client.exec(name,['python3','-c',COLLECT_SCRIPT,SANDBOX_OUT,str(MAX_SYNC_BYTES)],
                              workspace='default',no_login_shell=True,timeout_seconds=60)
        assert collected.exit_code==0,collected.stderr
        copied=probe_root/'copyout'
        materialize(json.loads(collected.stdout),copied)
        assert (copied/'workspace/src/agent.txt').read_text()=='from-sandbox','Copy-out must reach the host'
        script='import hashlib,json,pathlib; paths='+repr(BUNDLE_FILES)+'; print(json.dumps({name:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() for name,path in paths.items()}))'
        bundle=client.exec(name,['python3','-c',script],workspace='default',no_login_shell=True,timeout_seconds=15)
        assert bundle.exit_code==0
        evidence['bundle_sha256']=json.loads(bundle.stdout)
        names=subprocess.check_output([shutil.which('docker'),'ps','--format','{{.Names}}'],close_fds=False).decode().splitlines()
        supervisor=next(n for n in names if ref.id in n and n.endswith('-supervisor'))
        telemetry=subprocess.check_output([shutil.which('docker'),'inspect','--format',
            '{{range .Config.Env}}{{if eq . "OPENSHELL_TELEMETRY_ENABLED=false"}}disabled{{end}}{{end}}',supervisor],close_fds=False).decode().strip()
        assert telemetry=='disabled'
        workload=next(n for n in names if ref.id in n and not n.endswith('-supervisor'))
        network=subprocess.check_output([shutil.which('docker'),'inspect','--format','{{.HostConfig.NetworkMode}}',workload],close_fds=False).decode().strip()
        mounts=json.loads(subprocess.check_output([shutil.which('docker'),'inspect','--format','{{json .Mounts}}',workload],close_fds=False))
        assert network=='none'
        assert not any(m['Source'].endswith('docker.sock') or m['Type']=='bind' for m in mounts)
        evidence.update(version='0.1.7',telemetry_disabled=True,network_mode='none',sandbox_id=ref.id,agent_uid=args.uid,
            work_volume=args.volume,work_dir=str(work),transport='rpc-copy',host_mounts=False,sandbox_out=SANDBOX_OUT,
            agent_image=args.image,ca_sha256=hashlib.sha256((tls/'ca.crt').read_bytes()).hexdigest(),
            qualified_ns=time.time_ns(),expires_ns=time.time_ns()+86400000000000)
    finally:
        if ref:
            deletion=client.delete(name,workspace='default');client.wait_deleted(name,workspace='default',expected_sandbox_id=deletion.sandbox_id,timeout_seconds=120)
        client.close()
        shutil.rmtree(probe_root,ignore_errors=True)
    # Publish readiness only after the probe workload has been confirmed deleted.
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(evidence,indent=2));tmp.chmod(0o600);tmp.replace(out)
    print(json.dumps(evidence))


if __name__=='__main__':main()
