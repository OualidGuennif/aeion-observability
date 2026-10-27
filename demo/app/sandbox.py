"""The sole execution boundary for agent tools and generated code. No host or plain-Docker fallback."""
import hashlib
import json
import os
from pathlib import Path
import time

from settings import AGENT_UID, DATA, DEMO, OPENSHELL_STATE, WORK, WORK_VOLUME

VERSION = '0.1.5'
# Files the agent image must contain byte-for-byte (verified inside a live sandbox).
BUNDLE_FILES = {
    'agent/fs-helper.py': '/opt/demo/fs-helper.py',
    'fixtures/check-scenario.js': '/opt/demo/fixtures/check-scenario.js',
}
# Everything that defines what an admitted request, tool call or check can do.
PROTOCOL_FILES = [
    'tokenizers.json', 'agent/Dockerfile', 'agent/fs-helper.py', 'app/sandbox.py', 'app/runner.py', 'app/relay.py',
    'app/bridge.py', 'app/policy.py', 'app/token_budget.py', 'app/profiles.py', 'fixtures/check-scenario.js',
    'fixtures/scenarios.json', 'flue/package-lock.json', 'flue/src/db.ts', 'flue/src/provider.ts', 'flue/src/observe.ts',
    'flue/src/sandboxes/openshell.ts', 'flue/src/agents/coder.ts',
]


def protocol_hash():
    content = b''.join((DEMO / name).read_bytes() for name in PROTOCOL_FILES)
    return hashlib.sha256(os.environ['OPENSHELL_AGENT_IMAGE'].encode() + str(AGENT_UID).encode() + content).hexdigest()


def cli_qualified():
    try:
        value = json.loads((DATA / 'cli-qualification.json').read_text())
        return value['protocol_sha256'] == protocol_hash() and value['expires_ns'] > time.time_ns()
    except (OSError, ValueError, KeyError):
        return False


def connection(timeout=120):
    from openshell import SandboxClient, TlsConfig
    if (DATA / 'sandbox.blocked').exists():
        raise ValueError('SANDBOX_NOT_QUALIFIED')
    root = Path(os.environ.get('OPENSHELL_TLS_DIR', OPENSHELL_STATE / 'tls'))
    endpoint = os.environ['OPENSHELL_ENDPOINT']
    evidence = json.loads((root.parent / 'qualification/security.json').read_text())
    bundle = {name: hashlib.sha256((DEMO / name).read_bytes()).hexdigest() for name in BUNDLE_FILES}
    if (os.environ.get('OPENSHELL_TELEMETRY_ENABLED') != 'false'
            or evidence.get('version') != VERSION or evidence.get('telemetry_disabled') is not True
            or evidence.get('agent_image') != os.environ.get('OPENSHELL_AGENT_IMAGE')
            or evidence.get('agent_uid') != AGENT_UID
            or evidence.get('work_volume') != WORK_VOLUME or evidence.get('work_dir') != str(WORK.resolve())
            or evidence.get('bundle_sha256') != bundle
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
    # No network policy at all: model calls leave from the host harness, never from here.
    return pb.SandboxPolicy(version=1,
        filesystem=pb.FilesystemPolicy(include_workdir=True,
            read_only=['/bin', '/usr', '/lib', '/etc', '/proc', '/opt/demo', '/dev/urandom', '/var/log', str(root/'workspace')],
            read_write=['/tmp', '/dev/null', str(root/'workspace/src')]),
        landlock=pb.LandlockPolicy(compatibility='hard_requirement'),
        process=pb.ProcessPolicy(run_as_user=str(AGENT_UID), run_as_group=str(AGENT_UID)))


class Sandbox:
    def __init__(self, run, root, role='agent'):
        from openshell._proto import openshell_pb2 as pb
        from google.protobuf.json_format import ParseDict
        self.client = connection()
        self.name = 'ae-' + hashlib.sha256(str(root).encode()).hexdigest()[:10] + '-' + str(run['agents']) + role[0]
        self.ref = None
        self.closed = False
        spec = pb.SandboxSpec(template=pb.SandboxTemplate(image=os.environ['OPENSHELL_AGENT_IMAGE']),
                              policy=policy(root), command=['/bin/sleep', 'infinity'])
        # Only this run's subpath of the labeled work volume is visible; it is the host folder
        # under WORK, so files persist across fresh sandboxes. A root outside WORK fails here.
        ParseDict({'docker': {'mounts': [{'type': 'volume', 'source': WORK_VOLUME, 'target': str(root),
                                          'subpath': str(root.relative_to(WORK)), 'read_only': False}]}},
                  spec.template.driver_config)
        ParseDict({'limits': {'cpu': '1', 'memory': '1Gi'}}, spec.template.resources)
        try:
            self.ref = self.client.create(workspace='default', name=self.name, spec=spec,
                labels={'aeion.run.id': run['id'], 'aeion.role': role})
            self.client.wait_ready(self.name, workspace='default', timeout_seconds=120)
        except Exception:
            if self.ref is None:
                # Create may commit before an RPC timeout. Never assume no workload exists.
                (DATA / 'sandbox.blocked').write_text('Unknown create outcome requires operator requalification.\n')
            self.close()
            raise ValueError("SANDBOX_UNAVAILABLE") from None

    def exec(self, command, *, env=None, workdir=None, timeout=15, stdin=None):
        if self.closed:
            raise ValueError('SANDBOX_CLOSED')
        return self.client.exec(self.name, command, workspace='default', env=env, stdin=stdin,
                                workdir=str(workdir) if workdir else None, no_login_shell=True, timeout_seconds=timeout)

    def close(self):
        if self.closed:
            return
        try:
            if self.ref:
                result = self.client.delete(self.name, workspace='default')
                self.client.wait_deleted(self.name, workspace='default', expected_sandbox_id=result.sandbox_id, timeout_seconds=120)
            self.closed = True
        except Exception:
            (DATA / 'sandbox.blocked').write_text('Sandbox cleanup requires operator requalification.\n')
            raise ValueError('SANDBOX_STOP_FAILED') from None
        finally:
            self.client.close()
