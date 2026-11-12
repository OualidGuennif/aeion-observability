"""Missing, stale or drifted qualification cannot reach the gateway or start an agent."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import sandbox


class _UnreachableClient:
    """Qualification must refuse before any SDK object exists."""
    def __init__(self,*args,**kwargs):
        raise AssertionError('SandboxClient constructed for unqualified evidence')


class QualificationTests(unittest.TestCase):
    def test_missing_cli_evidence_is_closed(self):
        with patch.object(Path,'read_text',side_effect=FileNotFoundError):
            self.assertFalse(sandbox.cli_qualified())

    def test_expiry_image_drift_and_telemetry_never_connect(self):
        sdk=types.ModuleType('openshell');sdk.SandboxClient=_UnreachableClient;sdk.TlsConfig=_UnreachableClient
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'tls').mkdir();(root/'qualification').mkdir();(root/'tls/ca.crt').write_bytes(b'fixture-ca')
            evidence=dict(version=sandbox.VERSION,telemetry_disabled=True,agent_image='sha256:fixture',agent_uid=sandbox.AGENT_UID,work_volume=sandbox.WORK_VOLUME,work_dir=str(sandbox.WORK.resolve()),transport='rpc-copy',host_mounts=False,
                          ca_sha256=hashlib.sha256(b'fixture-ca').hexdigest(),expires_ns=time.time_ns()+10**12,
                          bundle_sha256={name:hashlib.sha256((Path(sandbox.__file__).resolve().parent.parent/name).read_bytes()).hexdigest() for name in sandbox.BUNDLE_FILES})
            for changes,flag in [({'expires_ns':0},'false'),({'agent_image':'different'},'false'),({'agent_uid':0},'false'),({'work_dir':'/elsewhere'},'false'),
                                 ({'ca_sha256':'different'},'false'),({'bundle_sha256':{}},'false'),({'host_mounts':True},'false'),({'transport':'old'},'false'),({},'true')]:
                with self.subTest(changes=changes,flag=flag):
                    (root/'qualification/security.json').write_text(json.dumps({**evidence,**changes}))
                    with patch.dict(os.environ,{'OPENSHELL_TLS_DIR':str(root/'tls'),
                              'OPENSHELL_ENDPOINT':'fixture.invalid:17670','OPENSHELL_AGENT_IMAGE':'sha256:fixture',
                              'OPENSHELL_TELEMETRY_ENABLED':flag}),patch.dict(sys.modules,{'openshell':sdk}):
                        with self.assertRaisesRegex(ValueError,'SANDBOX_NOT_QUALIFIED'):sandbox.connection()


class SandboxLifecycleTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        try:
            from openshell._proto import openshell_pb2, sandbox_pb2  # noqa: F401
            from google.protobuf.json_format import ParseDict  # noqa: F401
        except ImportError:
            proto_pkg = types.ModuleType('openshell._proto')
            pb_mock = types.SimpleNamespace(
                SandboxSpec=lambda **kw: types.SimpleNamespace(template=types.SimpleNamespace(resources={})),
                SandboxTemplate=lambda **kw: types.SimpleNamespace(),
                SandboxPolicy=lambda **kw: types.SimpleNamespace(),
                FilesystemPolicy=lambda **kw: types.SimpleNamespace(),
                LandlockPolicy=lambda **kw: types.SimpleNamespace(),
                ProcessPolicy=lambda **kw: types.SimpleNamespace(),
            )
            proto_pkg.openshell_pb2 = pb_mock
            proto_pkg.sandbox_pb2 = pb_mock
            sys.modules['openshell._proto'] = proto_pkg
            sys.modules['openshell._proto.openshell_pb2'] = pb_mock
            sys.modules['openshell._proto.sandbox_pb2'] = pb_mock
            if 'google.protobuf.json_format' not in sys.modules:
                json_format_mod = types.ModuleType('google.protobuf.json_format')
                json_format_mod.ParseDict = lambda *a, **kw: None
                sys.modules['google.protobuf.json_format'] = json_format_mod

    def test_sandbox_naming_uniqueness(self):
        fake_client = types.SimpleNamespace(
            create=lambda **kw: types.SimpleNamespace(sandbox_id='sb-1'),
            wait_ready=lambda *a, **kw: None,
            get=lambda *a, **kw: None,
            close=lambda: None
        )
        with patch.object(sandbox, 'connection', return_value=fake_client), \
             patch.dict(os.environ, {'OPENSHELL_AGENT_IMAGE': 'sha256:fixture'}):
            sb1 = sandbox.Sandbox({'id': 'run-alpha-1234', 'agents': 1}, Path('/work/r1'), role='coder', retries=1)
            sb2 = sandbox.Sandbox({'id': 'run-beta-5678', 'agents': 1}, Path('/work/r1'), role='coder', retries=1)
            # Distinct run IDs must yield distinct sandbox names
            self.assertNotEqual(sb1.name, sb2.name)
            # Both names must follow legal OpenShell identifier conventions
            import re
            self.assertTrue(re.match(r'^ae-[0-9a-f]{12}-\d+[a-z]$', sb1.name), f'Invalid name {sb1.name}')
            self.assertTrue(len(sb1.name) <= 19)

    def test_sandbox_init_retry_success(self):
        call_count = [0]
        def mock_create(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("transient docker daemon error")
            return types.SimpleNamespace(sandbox_id='sb-ok')

        fake_client = types.SimpleNamespace(
            create=mock_create,
            wait_ready=lambda *a, **kw: None,
            get=lambda *a, **kw: None,
            delete=lambda *a, **kw: types.SimpleNamespace(sandbox_id='sb-del'),
            wait_deleted=lambda *a, **kw: None,
            close=lambda: None
        )
        with patch.object(sandbox, 'connection', return_value=fake_client), \
             patch.object(time, 'sleep', return_value=None), \
             patch.dict(os.environ, {'OPENSHELL_AGENT_IMAGE': 'sha256:fixture'}):
            sb = sandbox.Sandbox({'id': 'run-retry', 'agents': 1}, Path('/work'), role='agent', retries=3)
            self.assertIsNotNone(sb.ref)
            self.assertEqual(call_count[0], 2)

    def test_sandbox_init_failure_without_lingering_does_not_block(self):
        fake_client = types.SimpleNamespace(
            create=lambda **kw: (_ for _ in ()).throw(RuntimeError("creation failed")),
            wait_ready=lambda *a, **kw: None,
            get=lambda *a, **kw: None,  # No lingering sandbox
            delete=lambda *a, **kw: None,
            wait_deleted=lambda *a, **kw: None,
            close=lambda: None
        )
        with tempfile.TemporaryDirectory() as folder:
            fake_data = Path(folder)
            blocked_file = fake_data / 'sandbox.blocked'
            with patch.object(sandbox, 'connection', return_value=fake_client), \
                 patch.object(sandbox, 'DATA', fake_data), \
                 patch.object(time, 'sleep', return_value=None), \
                 patch.dict(os.environ, {'OPENSHELL_AGENT_IMAGE': 'sha256:fixture'}):
                with self.assertRaisesRegex(ValueError, "SANDBOX_UNAVAILABLE"):
                    sandbox.Sandbox({'id': 'run-fail', 'agents': 1}, Path('/work'), role='agent', retries=2)
                # Since no lingering sandbox exists, sandbox.blocked must NOT be written
                self.assertFalse(blocked_file.exists())


if __name__=='__main__':unittest.main()
