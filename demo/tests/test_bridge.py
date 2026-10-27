"""Flue's OpenShell adapter through the bridge; a local fake sandbox stands in for OpenShell."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge import HELPER, SandboxBridge
from local_sandbox import LocalSandbox

FLUE = ROOT / "flue"
NODE = shutil.which("node")


def post(bridge, route, body, token=None):
    request = urllib.request.Request(bridge.url + route, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + (token or bridge.token), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.sandbox = LocalSandbox()
        self.bridge = SandboxBridge(self.sandbox)
        self.bridge.start()

    def tearDown(self):
        self.bridge.close()
        shutil.rmtree(self.folder)

    def test_token_and_request_validation(self):
        self.assertEqual(post(self.bridge, "/v1/fs", {"op": "exists", "path": "/"}, token="wrong")[0], 403)
        for body in ({"op": "read", "path": "relative"}, {"op": "chmod", "path": "/x"},
                     {"op": "write", "path": "/x", "data": "not base64!"}):
            self.assertEqual(post(self.bridge, "/v1/fs", body)[0], 400, body)
        for body in ({"command": ""}, {"command": "true", "env": {"BAD-NAME": "1"}}, {"command": "true", "timeoutMs": 0}):
            self.assertEqual(post(self.bridge, "/v1/exec", body)[0], 400, body)
        self.assertEqual(self.sandbox.calls, [])

    def test_helper_reports_missing_paths_without_failing_the_bridge(self):
        status, value = post(self.bridge, "/v1/fs", {"op": "read", "path": str(self.folder / "missing")})
        self.assertEqual((status, value["ok"]), (200, False))
        self.assertIn("No such file", value["error"])
        self.assertEqual(post(self.bridge, "/v1/fs", {"op": "rm", "path": str(self.folder / "missing"), "force": True})[1],
                         {"ok": True})

    @unittest.skipUnless(NODE and (FLUE / "node_modules/@flue/runtime").is_dir(), "node and demo/flue dependencies required")
    def test_flue_adapter_round_trip(self):
        script = """
import { openShellDriver } from './src/sandboxes/openshell.ts';
import { sandboxFromDriver } from '@flue/runtime';
const [url, token, cwd] = process.argv.slice(2);
const sandbox = sandboxFromDriver(openShellDriver({ url, token, cwd }), cwd);
await sandbox.writeFile('src/nested/a.js', 'export const a = 1;\\n');
await sandbox.writeFile('bin.dat', new Uint8Array([0, 255, 1]));
const out = {
  text: await sandbox.readFile('src/nested/a.js'),
  bytes: Array.from(await sandbox.readFileBuffer('bin.dat')),
  stat: await sandbox.stat('src/nested/a.js'),
  listing: await sandbox.readdir('src'),
  exists: [await sandbox.exists('src/nested'), await sandbox.exists('nope')],
  exec: await sandbox.exec('echo "$PWD" && cat src/nested/a.js >&2 && exit 3', { env: { AEION_TEST: '1' } }),
};
await sandbox.rm('src', { recursive: true });
out.removed = !(await sandbox.exists('src'));
console.log(JSON.stringify(out));
"""
        done = subprocess.run([NODE, "--input-type=module", "-", self.bridge.url, self.bridge.token, str(self.folder)],
                              input=script.encode(), capture_output=True, cwd=FLUE, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr.decode()[-2000:])
        out = json.loads(done.stdout)
        self.assertEqual(out["text"], "export const a = 1;\n")
        self.assertEqual(out["bytes"], [0, 255, 1])
        self.assertTrue(out["stat"]["isFile"] and not out["stat"]["isDirectory"] and out["stat"]["size"] == 20)
        self.assertEqual(out["listing"], ["nested"])
        self.assertEqual(out["exists"], [True, False])
        self.assertEqual(out["exec"], {"stdout": str(self.folder) + "\n", "stderr": "export const a = 1;\n", "exitCode": 3})
        self.assertTrue(out["removed"])
        # Every verb ran as a fixed argv command; file content never became a shell argument.
        self.assertTrue(all(c[:3] == ["python3", "-I", HELPER] or c[:2] == ["/bin/bash", "-c"] for c in self.sandbox.calls))
        self.assertNotIn(base64.b64encode(b"export const a = 1;\n").decode(), json.dumps(self.sandbox.calls))


if __name__ == "__main__":
    unittest.main()
