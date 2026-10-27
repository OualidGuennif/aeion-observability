"""The sole agent execution boundary. No local CLI/Docker execution fallback."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import urlparse

VERSION = '0.1.5'
AGENT_TIMEOUT_SECONDS = 360


def protocol_hash():
    base = Path(__file__).resolve().parent.parent
    files = ['context-gate.mjs', 'gate-policy.mjs', 'tokenizers.json', 'agent/models.json',
             'agent/Dockerfile', 'agent/process.py', 'app/sandbox.py', 'app/runner.py',
             'app/relay.py', 'app/token_budget.py', 'app/profiles.py', 'fixtures/check-scenario.js', 'fixtures/scenarios.json']
    content = b''.join((base / name).read_bytes() for name in files)
    return hashlib.sha256(os.environ['OPENSHELL_AGENT_IMAGE'].encode() + content).hexdigest()


def cli_qualified():
    try:
        value = json.loads(Path('/data/cli-qualification.json').read_text())
        return value['protocol_sha256'] == protocol_hash() and value['expires_ns'] > time.time_ns()
    except (OSError, ValueError, KeyError):
        return False


def connection(timeout=30):
    from openshell import SandboxClient, TlsConfig
    if Path('/data/sandbox.blocked').exists():
        raise ValueError('SANDBOX_NOT_QUALIFIED')
    root = Path(os.environ.get('OPENSHELL_TLS_DIR', '/gateway/tls'))
    endpoint = os.environ['OPENSHELL_ENDPOINT']
    evidence = json.loads((root.parent / 'qualification/security.json').read_text())
    if (os.environ.get('OPENSHELL_TELEMETRY_ENABLED') != 'false'
            or evidence.get('version') != VERSION or evidence.get('telemetry_disabled') is not True
            or evidence.get('agent_image') != os.environ.get('OPENSHELL_AGENT_IMAGE')
            or evidence.get('expires_ns', 0) < time.time_ns()
            or evidence.get('ca_sha256') != hashlib.sha256((root / 'ca.crt').read_bytes()).hexdigest()):
        raise ValueError('SANDBOX_NOT_QUALIFIED')
    client = SandboxClient(endpoint, tls=TlsConfig(ca_path=root/'ca.crt', cert_path=root/'client/tls.crt', key_path=root/'client/tls.key'), timeout=timeout)
    try:
        if client.health().version != VERSION:
            raise ValueError('SANDBOX_VERSION_MISMATCH')
    except Exception:
        client.close()
        raise
    return client


def policy(root):
    from openshell._proto import sandbox_pb2 as pb
    url = urlparse(os.environ['DEMO_RELAY_URL'])
    if url.scheme != 'http' or not url.hostname or url.port != 8091 or url.path != '/v1':
        raise ValueError('INVALID_RELAY_CONFIGURATION')
    return pb.SandboxPolicy(version=1,
        filesystem=pb.FilesystemPolicy(include_workdir=True,
            read_only=['/bin','/usr','/lib','/etc','/proc','/opt/demo','/dev/urandom','/var/log',str(root/'workspace')],
            read_write=['/tmp','/dev/null',str(root/'workspace/src'),str(root/'runtime')]),
        landlock=pb.LandlockPolicy(compatibility='hard_requirement'),
        process=pb.ProcessPolicy(run_as_user='10001',run_as_group='10001'),
        network_policies={'aeion_relay':pb.NetworkPolicyRule(name='aeion-counted-inference-only',
            endpoints=[pb.NetworkEndpoint(host=url.hostname,port=8091,protocol='rest',enforcement=1,
                rules=[pb.L7Rule(allow=pb.L7Allow(method='POST',path='/v1/chat/completions'))])],
            binaries=[pb.NetworkBinary(path='/usr/local/lib/node_modules/opencode-ai/bin/opencode.exe')])})


class Sandbox:
    def __init__(self, run, root):
        from openshell._proto import openshell_pb2 as pb
        from google.protobuf.json_format import ParseDict
        self.client = connection()
        self.runtime = root / 'runtime'
        self.runtime.mkdir(mode=0o700)
        os.chown(self.runtime,10001,10001)
        # OpenCode tries to install its plugin SDK in writable config directories.
        # This lab uses local JS hooks and bundled providers; keep config immutable/offline.
        config=self.runtime/'config'/'opencode'
        config.mkdir(parents=True,mode=0o555)
        config.parent.chmod(0o555)
        self.name = 'ae-' + hashlib.sha256(str(root).encode()).hexdigest()[:10] + '-' + str(run['agents'])
        self.ref = None
        self.process = None
        self.closed = False
        spec = pb.SandboxSpec(template=pb.SandboxTemplate(image=os.environ['OPENSHELL_AGENT_IMAGE']),
                              policy=policy(root), command=['/bin/sleep','infinity'])
        ParseDict({'docker':{'mounts':[{'type':'volume','source':os.environ['DEMO_WORK_VOLUME'],
                   'target':str(root),'subpath':str(root.relative_to('/work')),'read_only':False}]}},spec.template.driver_config)
        ParseDict({'limits':{'cpu':'1','memory':'1Gi'}},spec.template.resources)
        try:
            self.ref = self.client.create(workspace='default',name=self.name,spec=spec,
                labels={'aeion.run.id':run['id'],'aeion.role':'build-or-check'})
            self.client.wait_ready(self.name,workspace='default',timeout_seconds=120)
        except Exception:
            if self.ref is None:
                # Create may commit before an RPC timeout. Never assume no workload exists.
                Path('/data/sandbox.blocked').write_text('Unknown create outcome requires operator requalification.\n')
            self.close()
            shutil.rmtree(self.runtime)
            raise ValueError("SANDBOX_UNAVAILABLE") from None

    def exec(self, command, *, env=None, workdir=None, timeout=15):
        if self.closed:
            raise ValueError('SANDBOX_CLOSED')
        return self.client.exec(self.name,command,workspace='default',env=env,workdir=str(workdir) if workdir else None,
                                no_login_shell=True,timeout_seconds=timeout)

    def start(self, command, env, workdir):
        self.process = RemoteProcess(self,command,env,workdir)
        return self.process

    def close(self):
        if self.closed:
            return
        try:
            if self.ref:
                result = self.client.delete(self.name,workspace='default')
                self.client.wait_deleted(self.name,workspace='default',expected_sandbox_id=result.sandbox_id,timeout_seconds=120)
            self.closed = True
        except Exception:
            Path('/data/sandbox.blocked').write_text('Sandbox cleanup requires operator requalification.\n')
            raise ValueError('SANDBOX_STOP_FAILED') from None
        finally:
            self.client.close()



class RemoteProcess:
    def __init__(self, sandbox, command, env, workdir):
        self.sandbox, self.pid, self.returncode = sandbox,None,None
        self.finished,self.started = threading.Event(),threading.Event()
        read_fd,write_fd = os.pipe()
        self.stdout = os.fdopen(read_fd,'rb',buffering=0)
        self.error = False
        def receive():
            from openshell import ExecChunk, ExecResult
            first = b''
            try:
                stream = sandbox.client.exec_stream(sandbox.name,['python3','/opt/demo/agent-process.py','run',*command],
                    workspace='default',env=env,workdir=str(workdir),no_login_shell=True,timeout_seconds=AGENT_TIMEOUT_SECONDS)
                for item in stream:
                    if isinstance(item,ExecChunk) and item.stream=='stdout':
                        block=item.data
                        if self.pid is None:
                            first+=block
                            if len(first)>4096: raise ValueError('CLI_PROTOCOL_ERROR')
                            if b'\n' not in first: continue
                            line,block=first.split(b'\n',1)
                            self.pid=json.loads(line)['aeion_process_pid']
                            if type(self.pid) is not int or self.pid<=1: raise ValueError('CLI_PROTOCOL_ERROR')
                            self.started.set()
                        if block:
                            view=memoryview(block)
                            while view: view=view[os.write(write_fd,view):]
                    elif isinstance(item,ExecResult): self.returncode=item.exit_code
            except Exception:
                self.error=True
            finally:
                os.close(write_fd);self.started.set();self.finished.set()
        self.thread=threading.Thread(target=receive,daemon=True);self.thread.start()
        if not self.started.wait(20) or self.pid is None:
            self.stdout.close()
            raise ValueError('SANDBOX_EXEC_FAILED')

    def poll(self):
        if not self.finished.is_set():
            return None
        return self.returncode if self.returncode is not None else 1

    def wait(self,timeout):
        if not self.finished.wait(timeout) or self.error:
            raise ValueError('SANDBOX_EXEC_FAILED')
        return self.returncode
