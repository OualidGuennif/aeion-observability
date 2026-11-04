"""The agent sandbox receives no host mount and its exec defaults to sandbox-owned /tmp."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import sandbox


@unittest.skipUnless(
    importlib.util.find_spec('openshell') and importlib.util.find_spec('openshell._proto'),
    'OpenShell SDK required',
)
class UnmountedSandboxTests(unittest.TestCase):
    def test_creation_has_no_mounts_or_host_write_paths(self):
        client = Mock()
        client.create.return_value = SimpleNamespace(id='fixture')
        with tempfile.TemporaryDirectory() as folder, patch.object(sandbox, 'connection', return_value=client), \
                patch.dict('os.environ', {'OPENSHELL_AGENT_IMAGE':'synthetic-agent-image'}):
            root = Path(folder) / 'run'
            box = sandbox.Sandbox({'id': 'fixture', 'agents': 1}, root)
            try:
                spec = client.create.call_args.kwargs['spec']
                self.assertFalse(spec.template.driver_config.ListFields())
                self.assertFalse(spec.policy.filesystem.include_workdir)
                self.assertNotIn(str(root), str(spec.policy))
                box.exec(['true'])
                self.assertEqual(client.exec.call_args.kwargs['workdir'], '/tmp')
            finally:
                box.close()


if __name__ == '__main__':
    unittest.main()
