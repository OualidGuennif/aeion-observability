import os
import subprocess
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.freeze import FreezeError, freeze_build
from factory.artifact import ArtifactError, changed_entries, scoped_texts, validate_artifact, _path_problem


def feat(fid, depends_on=(), parallel=False, write=None):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": parallel, "phase": "P0", "tier": 3,
        "write_paths": write or ["demo/forum/product/"], "depends_on": list(depends_on),
        "file": f"{fid}.md",
    }


def catalog():
    return Catalog({"schema_version": 2, "count": 1, "features": [feat("001")]})


def config(**overrides):
    base = {"profile": "fake", "mode": "fake", "deadline_ns": 60_000_000_000,
            "step_cap": 100, "context_limit": 250_000, "cost_reservation_usd": "0.00"}
    base.update(overrides)
    return base


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.spec_dir = Path(self.tmp.name) / "specs"
        self.spec_dir.mkdir()
        (self.spec_dir / "001.md").write_text("# 001\n")
        self.cat = catalog()

    def test_freeze_binds_all_identity_fields(self):
        frozen = freeze_build({"build_id": "b1", "feature_id": "001"}, self.cat, self.spec_dir, "abc123", config())
        self.assertEqual(frozen.feature_id, "001")
        self.assertEqual(frozen.base_sha, "abc123")
        self.assertEqual(frozen.manifest_digest, self.cat.digest)
        self.assertEqual(frozen.tier, 3)
        self.assertEqual(frozen.step_cap, 100)

    def test_missing_spec_is_refused(self):
        (self.spec_dir / "001.md").unlink()
        with self.assertRaisesRegex(FreezeError, "missing_spec"):
            freeze_build({"build_id": "b1", "feature_id": "001"}, self.cat, self.spec_dir, "abc", config())

    def test_missing_bound_is_refused(self):
        with self.assertRaisesRegex(FreezeError, "missing_bound:step_cap"):
            freeze_build({"build_id": "b1", "feature_id": "001"}, self.cat, self.spec_dir, "abc", config(step_cap=None))
        with self.assertRaisesRegex(FreezeError, "missing_bound:base_sha"):
            freeze_build({"build_id": "b1", "feature_id": "001"}, self.cat, self.spec_dir, None, config())

    def test_digest_is_stable(self):
        a = freeze_build({"build_id": "b1", "feature_id": "001"}, self.cat, self.spec_dir, "abc", config())
        b = freeze_build({"build_id": "b1", "feature_id": "001"}, self.cat, self.spec_dir, "abc", config())
        self.assertEqual(a.digest(), b.digest())


def init_repo(root):
    (root / "demo" / "forum" / "product").mkdir(parents=True)
    (root / "demo" / "forum" / "product" / "base.txt").write_text("base\n")
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "base"], check=True)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        init_repo(self.repo)
        self.scopes = ["demo/forum/product/"]

    def test_in_scope_change_accepted(self):
        (self.repo / "demo/forum/product/app.py").write_text("x")
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertTrue(verdict["accepted"])
        self.assertIn("demo/forum/product/app.py", verdict["allowed"])
        self.assertIsNotNone(verdict["digest"])

    def test_scoped_texts_keep_allowed_paths_when_another_path_is_rejected(self):
        (self.repo / "demo/forum/product/app.py").write_text("kept\n")
        (self.repo / "demo/factory").mkdir(parents=True)
        (self.repo / "demo/factory/evil.py").write_text("no\n")
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertNotIn("files", verdict)
        self.assertEqual(scoped_texts(self.repo, self.scopes), {"demo/forum/product/app.py": "kept\n"})

    def test_out_of_scope_change_rejected(self):
        (self.repo / "demo/factory").mkdir(parents=True)
        (self.repo / "demo/factory/evil.py").write_text("x")
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertEqual(verdict["rejected"][0]["reason"], "out_of_scope")

    def test_symlink_rejected(self):
        os.symlink("target", self.repo / "demo/forum/product/link")
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertTrue(any(r["reason"] == "symlink" for r in verdict["rejected"]))

    def test_rename_out_of_scope_rejected(self):
        (self.repo / "demo/factory").mkdir(parents=True)
        subprocess.run(["git", "-C", str(self.repo), "mv", "demo/forum/product/base.txt", "demo/factory/moved.txt"], check=True)
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertTrue(any("->" in r["path"] for r in verdict["rejected"]))

    def test_rename_within_scope_is_held_as_unsupported(self):
        subprocess.run(["git", "-C", str(self.repo), "mv", "demo/forum/product/base.txt", "demo/forum/product/moved.txt"], check=True)
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertEqual(verdict["rejected"][0]["reason"], "unsupported_effect:rename")

    def test_deletion_is_held_as_unsupported(self):
        (self.repo / "demo/forum/product/base.txt").unlink()
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertEqual(verdict["rejected"][0]["reason"], "unsupported_effect:D")

    def test_binary_content_is_refused(self):
        (self.repo / "demo/forum/product/blob.bin").write_bytes(b"\x00\x01")
        verdict = validate_artifact(self.repo, self.scopes)
        self.assertFalse(verdict["accepted"])
        self.assertEqual(verdict["rejected"][0]["reason"], "binary_content")

    def test_digest_covers_the_bytes_not_only_the_paths(self):
        path = self.repo / "demo/forum/product/app.py"
        path.write_text("one\n")
        first = validate_artifact(self.repo, self.scopes)
        path.write_text("two\n")
        second = validate_artifact(self.repo, self.scopes)
        self.assertTrue(first["accepted"] and second["accepted"])
        self.assertNotEqual(first["digest"], second["digest"])
        self.assertEqual(second["files"], {"demo/forum/product/app.py": "two\n"})

    def test_path_problem_string_cases(self):
        self.assertEqual(_path_problem("/etc/passwd", self.repo, self.scopes), "traversal_or_absolute")
        self.assertEqual(_path_problem("../sibling", self.repo, self.scopes), "traversal_or_absolute")
        self.assertEqual(_path_problem("demo/forum/product/.git/config", self.repo, self.scopes), "git_metadata")
        self.assertEqual(_path_problem("demo/app/x", self.repo, self.scopes), "out_of_scope")
        self.assertIsNone(_path_problem("demo/forum/product/x", self.repo, self.scopes))


if __name__ == "__main__":
    unittest.main()
