"""The OpenShell security proof is refreshed before it expires, and never deleted first."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HOUR_NS = 3_600_000_000_000
NOW = 1_700_000_000_000_000_000


def load():
    path = Path(__file__).resolve().parents[1] / "openshell" / "security_window.py"
    spec = importlib.util.spec_from_file_location("aeion_openshell_security_window", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SecurityWindowTests(unittest.TestCase):
    def setUp(self):
        self.window = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "qualification" / "security.json"

    def write(self, expires):
        self.window.publish_evidence(self.path, {"expires_ns": expires})

    def test_an_hour_or_more_left_does_not_call_the_probe(self):
        self.write(NOW + HOUR_NS)
        def probe():
            raise AssertionError("probe")
        self.assertTrue(self.window.ensure_fresh(self.path, probe, now_ns=NOW))
        self.assertFalse(self.window.needs_refresh(self.path, now_ns=NOW))

    def test_under_an_hour_runs_the_probe_and_keeps_a_published_replacement(self):
        self.write(NOW + HOUR_NS - 1)
        seen = []

        def probe():
            seen.append(self.path.read_text(encoding="utf-8"))
            self.window.publish_evidence(self.path, {"expires_ns": NOW + 24 * HOUR_NS})

        self.assertTrue(self.window.ensure_fresh(self.path, probe, now_ns=NOW))
        self.assertEqual(len(seen), 1)
        self.assertEqual(json.loads(self.path.read_text())["expires_ns"], NOW + 24 * HOUR_NS)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_a_failed_probe_keeps_an_unexpired_file_and_still_allows_the_open(self):
        self.write(NOW + HOUR_NS - 1)
        before = self.path.read_bytes()

        def probe():
            raise RuntimeError("probe_failed")

        self.assertTrue(self.window.ensure_fresh(self.path, probe, now_ns=NOW))
        self.assertEqual(self.path.read_bytes(), before)

    def test_a_failed_probe_on_an_expired_or_missing_file_refuses_the_open(self):
        self.write(NOW - 1)
        before = self.path.read_bytes()

        def probe():
            raise RuntimeError("probe_failed")

        self.assertFalse(self.window.ensure_fresh(self.path, probe, now_ns=NOW))
        self.assertEqual(self.path.read_bytes(), before)
        self.path.unlink()
        self.assertFalse(self.window.ensure_fresh(self.path, probe, now_ns=NOW))
        self.assertFalse(self.path.exists())

    def test_the_host_probe_does_not_delete_the_proof_before_it_runs(self):
        text = (Path(__file__).resolve().parents[1] / "openshell" / "qualify.py").read_text(encoding="utf-8")
        self.assertNotIn("unlink", text)
        self.assertIn("publish_evidence", text)


if __name__ == "__main__":
    unittest.main()
