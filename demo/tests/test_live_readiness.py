"""The readiness diagnostic reports; it must never import the HTTP server or bind a socket."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1]


def run_diagnostic(body):
    with tempfile.TemporaryDirectory() as state:
        environment = {"PATH": os.environ.get("PATH", ""), "AEION_LOCAL_DIR": state,
                       "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([sys.executable, "-c", body], cwd=str(DEMO), env=environment,
                              capture_output=True, text=True, timeout=60)


class LiveReadinessTests(unittest.TestCase):
    def test_importing_the_diagnostic_does_not_import_the_server(self):
        result = run_diagnostic(
            "import sys; sys.path.insert(0, 'factory'); import live_readiness; "
            "assert 'server' not in sys.modules; print('imported')")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "imported")

    def test_the_report_uses_the_sandbox_helper_and_never_the_server(self):
        body = (
            "import json, sys\n"
            "sys.path.insert(0, 'factory')\n"
            "import live_readiness\n"
            "class Client:\n"
            "    def close(self): pass\n"
            "import sandbox\n"
            "sandbox.connection = lambda timeout=2: Client()\n"
            "report = live_readiness.build_report()\n"
            "print(json.dumps({'server': 'server' in sys.modules, "
            "'ready': report.get('sandbox_ready')}))\n")
        result = run_diagnostic(body)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"server": False, "ready": True})

    def test_the_source_does_not_import_the_application_entry_point(self):
        source = (DEMO / "factory" / "live_readiness.py").read_text()
        self.assertNotIn("from server import", source)
        self.assertNotIn("import server", source)


if __name__ == "__main__":
    unittest.main()
