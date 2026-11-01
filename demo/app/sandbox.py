"""The sole execution boundary for agent tools and generated code. No host or plain-Docker fallback."""
import base64
import hashlib
import json
import os
from pathlib import Path
import time

from settings import AGENT_UID, DATA, DEMO, OPENSHELL_STATE, WORK, WORK_VOLUME

VERSION = '0.1.5'
# Sandbox-owned work directory. Writes here stay inside the sandbox, which is the only
# transport that is reliable on Docker Desktop: host-backed volume writes land but the
# syscall returns EACCES, so results are collected over the exec channel instead.
SANDBOX_OUT = '/tmp/aeion-out'
MAX_SYNC_BYTES = 8 * 1024 * 1024
COLLECT_SCRIPT = r'''
import base64, json, os, sys
root, limit = sys.argv[1], int(sys.argv[2])
items, total = {}, 0
for base, _, files in os.walk(root):
    for name in files:
        path = os.path.join(base, name)
        with open(path, 'rb') as handle:
            data = handle.read()
        total += len(data)
        if total > limit:
            raise SystemExit('sync_too_large')
        items[os.path.relpath(path, root)] = base64.b64encode(data).decode('ascii')
print(json.dumps(items))
'''
SEED_SCRIPT = r'''
import base64, json, os, sys
root = sys.argv[1]
items = json.loads(sys.stdin.read())
written = 0
for relative, payload in items.items():
    if os.path.isabs(relative) or '..' in relative.split('/'):
        raise SystemExit('seed_path')
    target = os.path.join(root, relative)
    folder = os.path.dirname(target)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(target, 'wb') as handle:
        handle.write(base64.b64decode(payload))
    written += 1
print(written)
'''


def materialize(items, destination):
    """Write collected sandbox files to the host, refusing anything outside the destination.

    A file the sandbox created on the mounted volume belongs to the sandbox UID, so the host
    user cannot overwrite it in place; the entry is removed and recreated instead.
    """
    destination = Path(destination)
    written = []
    for relative, payload in items.items():
        parts = Path(relative).parts
        if not relative or relative.startswith('/') or '\\' in relative or '..' in parts:
            raise ValueError('SANDBOX_SYNC_PATH')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = base64.b64decode(payload)
        if target.is_file() and not target.is_symlink() and target.read_bytes() == data:
            continue
        try:
            target.write_bytes(data)
        except PermissionError:
            try:
                target.unlink(missing_ok=True)
                target.write_bytes(data)
            except PermissionError as error:
                raise ValueError('SANDBOX_SYNC_TARGET_LOCKED') from error
        written.append(str(relative))
    return written

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
    'flue/src/sandboxes/openshell.ts', 'flue/src/agents/coder.ts', 'app/triage.py', 'fixtures/triage.json',
    'flue/src/sandboxes/restricted-local.ts', 'flue/src/skills/local-change/SKILL.md', 'flue/src/agents/local-assistant.ts',
    'flue/src/tools/submit-triage.ts', 'flue/src/agents/triage.ts',
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

    def seed_in(self, files, destination=SANDBOX_OUT):
        """Copy host files into the sandbox work directory before an agent starts."""
        encoded = {}
        total = 0
        for relative, data in files.items():
            blob = base64.b64encode(data).decode("ascii")
            total += len(blob)
            if total > MAX_SYNC_BYTES:
                raise ValueError('SANDBOX_SEED_TOO_LARGE')
            encoded[relative] = blob
        result = self.exec(['python3', '-c', SEED_SCRIPT, destination],
                           stdin=json.dumps(encoded).encode("utf-8"), timeout=60)
        if result.exit_code != 0:
            raise ValueError('SANDBOX_SEED_FAILED')
        return int(result.stdout.strip() or 0)

    def collect(self, source=SANDBOX_OUT):
        """Return {relative path: base64 bytes} for everything under a sandbox directory."""
        result = self.exec(['python3', '-c', COLLECT_SCRIPT, source, str(MAX_SYNC_BYTES)], timeout=60)
        if result.exit_code != 0:
            raise ValueError('SANDBOX_SYNC_FAILED')
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise ValueError('SANDBOX_SYNC_UNREADABLE') from exc

    def sync_out(self, destination, source=SANDBOX_OUT):
        """Copy a sandbox work directory to the host over the exec channel."""
        return materialize(self.collect(source), destination)

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
