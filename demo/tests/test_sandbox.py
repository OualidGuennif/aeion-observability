"""Missing, stale or drifted qualification cannot reach the gateway or start an agent."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import sandbox
try:
    import openshell
except ImportError:
    openshell=None


class QualificationTests(unittest.TestCase):
    def test_missing_cli_evidence_is_closed(self):
        with patch.object(Path,'read_text',side_effect=FileNotFoundError):
            self.assertFalse(sandbox.cli_qualified())

    @unittest.skipUnless(openshell,'OpenShell SDK in controller required')
    def test_expiry_image_drift_and_telemetry_never_connect(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'tls').mkdir();(root/'qualification').mkdir();(root/'tls/ca.crt').write_bytes(b'fixture-ca')
            evidence=dict(version='0.1.5',telemetry_disabled=True,agent_image='sha256:fixture',agent_uid=sandbox.AGENT_UID,
                          ca_sha256=hashlib.sha256(b'fixture-ca').hexdigest(),expires_ns=time.time_ns()+10**12,
                          bundle_sha256={name:hashlib.sha256((Path(sandbox.__file__).resolve().parent.parent/name).read_bytes()).hexdigest() for name in sandbox.BUNDLE_FILES})
            for changes,flag in [({'expires_ns':0},'false'),({'agent_image':'different'},'false'),({'agent_uid':0},'false'),
                                 ({'ca_sha256':'different'},'false'),({'bundle_sha256':{}},'false'),({},'true')]:
                with self.subTest(changes=changes,flag=flag):
                    (root/'qualification/security.json').write_text(json.dumps({**evidence,**changes}))
                    with patch.dict(os.environ,{'OPENSHELL_TLS_DIR':str(root/'tls'),
                              'OPENSHELL_ENDPOINT':'fixture.invalid:17670','OPENSHELL_AGENT_IMAGE':'sha256:fixture',
                              'OPENSHELL_TELEMETRY_ENABLED':flag}),patch('openshell.SandboxClient') as client:
                        with self.assertRaisesRegex(ValueError,'SANDBOX_NOT_QUALIFIED'):sandbox.connection()
                        client.assert_not_called()


if __name__=='__main__':unittest.main()
