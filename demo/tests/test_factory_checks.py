import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.checks import DEFAULT_CHECKS, ProtectedChecks, scope_check, spec_unchanged_check
from factory.freeze import freeze_build
from factory.manifest import Catalog


def feat(fid):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum/product/"], "depends_on": [], "file": f"{fid}.md",
    }


def config():
    return {"profile": "fake", "mode": "fake", "deadline_ns": 60_000_000_000,
            "step_cap": 100, "context_limit": 250_000, "cost_reservation_usd": "0.00"}


class ProtectedChecksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.spec_dir = Path(self.tmp.name) / "specs"
        self.spec_dir.mkdir()
        (self.spec_dir / "001.md").write_text("# 001\n")
        self.cat = Catalog({"schema_version": 2, "count": 1, "features": [feat("001")]})
        self.frozen = freeze_build({"build_id": "b1", "feature_id": "001"},
                                   self.cat, self.spec_dir, "abc", config())
        self.checks = ProtectedChecks(DEFAULT_CHECKS)

    def accepted(self, spec_digest=None):
        return {"accepted": True, "allowed": ["demo/forum/product/x.md"], "digest": "d",
                "spec_digest": spec_digest if spec_digest is not None else self.frozen.spec_digest}

    def test_all_checks_pass(self):
        verdict = self.checks.verdict(["scope", "spec_unchanged"], self.frozen, self.accepted())
        self.assertEqual(verdict["status"], "passed")
        self.assertEqual(verdict["results"]["scope"]["status"], "passed")

    def test_scope_fails_on_rejected_artifact(self):
        verdict = self.checks.verdict(["scope", "spec_unchanged"], self.frozen,
                                      {"accepted": False, "spec_digest": self.frozen.spec_digest})
        self.assertEqual(verdict["status"], "failed")
        self.assertEqual(verdict["results"]["scope"]["status"], "failed")

    def test_spec_unchanged_fails_on_mismatch(self):
        verdict = self.checks.verdict(["scope", "spec_unchanged"], self.frozen, self.accepted("tampered"))
        self.assertEqual(verdict["status"], "failed")
        self.assertEqual(verdict["results"]["spec_unchanged"]["status"], "failed")

    def test_missing_required_check_is_qualification_missing(self):
        verdict = self.checks.verdict(["scope", "nonexistent_check"], self.frozen, self.accepted())
        self.assertEqual(verdict["status"], "qualification_missing")
        self.assertEqual(verdict["results"]["nonexistent_check"]["status"], "qualification_missing")

    def test_bundle_digest_is_stable_and_order_independent(self):
        a = ProtectedChecks({"x": scope_check, "y": spec_unchanged_check})
        b = ProtectedChecks({"y": spec_unchanged_check, "x": scope_check})
        self.assertEqual(a.bundle_digest(), b.bundle_digest())

    def test_scope_check_direct(self):
        self.assertTrue(scope_check(self.frozen, self.accepted())[0])
        self.assertFalse(scope_check(self.frozen, {"accepted": False})[0])


if __name__ == "__main__":
    unittest.main()
