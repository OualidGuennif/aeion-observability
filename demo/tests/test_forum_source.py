"""The demo's product snapshot stays owned by the product repository and drift is refused."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forum"))
import source

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True, env=GIT_ENV)


def init(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=GIT_ENV)
    # Fixture commits must not spawn hooks/automatic repacking beyond directory cleanup.
    git(root, "config", "core.hooksPath", "/dev/null")
    git(root, "config", "maintenance.auto", "false")
    git(root, "config", "gc.auto", "0")


def commit(root, message="test"):
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)


def product_with(path, text):
    """A temporary product repository with one committed file."""
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    init(root)
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    commit(root)
    return directory, root, git(root, "rev-parse", "HEAD").stdout.strip()


def snapshot_with(commit_sha, files):
    """A temporary checkout whose source pin and lock cover `files` (path -> text)."""
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    init(root)
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (root / source.SOURCE).parent.mkdir(parents=True, exist_ok=True)
    (root / source.SOURCE).write_text(json.dumps({
        "repo": "https://example.invalid/product", "commit": commit_sha,
        "paths": ["demo/forum-app"],
    }), encoding="utf-8")
    (root / source.LOCK).write_text(json.dumps({
        "commit": commit_sha,
        "files": {path: hashlib.sha256(text.encode()).hexdigest() for path, text in files.items()},
    }), encoding="utf-8")
    commit(root)
    return directory, root


class SourceSnapshotTests(unittest.TestCase):
    def test_the_repository_snapshot_matches_its_lock(self):
        report = source.check()
        self.assertTrue(report["ok"], report["drift"])
        self.assertEqual(report["files"], 53)

    def test_a_hand_edit_is_drift(self):
        snapshot_dir, root = snapshot_with("a" * 40, {"demo/forum-app/A.java": "class A {}"})
        self.addCleanup(snapshot_dir.cleanup)
        (root / "demo/forum-app/A.java").write_text("class A { int changed; }", encoding="utf-8")
        report = source.check(root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["drift"]["changed"], ["demo/forum-app/A.java"])

    def test_an_extra_tracked_file_is_drift(self):
        snapshot_dir, root = snapshot_with("a" * 40, {"demo/forum-app/A.java": "class A {}"})
        self.addCleanup(snapshot_dir.cleanup)
        (root / "demo/forum-app/Extra.java").write_text("class Extra {}", encoding="utf-8")
        commit(root, "extra")
        report = source.check(root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["drift"]["unexpected"], ["demo/forum-app/Extra.java"])

    def test_refresh_restores_the_pin_and_drops_a_stale_file(self):
        product_dir, product, commit_sha = product_with("demo/forum-app/A.java", "class A { int pinned; }")
        snapshot_dir, root = snapshot_with(commit_sha, {
            "demo/forum-app/A.java": "class A {}",
            "demo/forum-app/Stale.java": "class Stale {}",
        })
        self.addCleanup(product_dir.cleanup)
        self.addCleanup(snapshot_dir.cleanup)
        report = source.refresh(root=root, product=product)
        self.assertEqual(report, {"commit": commit_sha, "files": 1, "removed": 1})
        self.assertEqual((root / "demo/forum-app/A.java").read_text(encoding="utf-8"),
                         "class A { int pinned; }")
        self.assertFalse((root / "demo/forum-app/Stale.java").exists())
        self.assertTrue(source.check(root)["ok"])

    def test_refresh_refuses_a_dirty_snapshot(self):
        product_dir, product, commit_sha = product_with("demo/forum-app/A.java", "class A { int pinned; }")
        snapshot_dir, root = snapshot_with(commit_sha, {"demo/forum-app/A.java": "class A {}"})
        self.addCleanup(product_dir.cleanup)
        self.addCleanup(snapshot_dir.cleanup)
        (root / "demo/forum-app/A.java").write_text("local edit", encoding="utf-8")
        with self.assertRaises(source.SourceError) as caught:
            source.refresh(root=root, product=product)
        self.assertEqual(str(caught.exception), "mirror_dirty")

    def test_refresh_refuses_a_symlink_in_the_product_snapshot(self):
        product_dir = tempfile.TemporaryDirectory()
        product = Path(product_dir.name)
        self.addCleanup(product_dir.cleanup)
        init(product)
        (product / "demo/forum-app").mkdir(parents=True)
        (product / "demo/forum-app/A.java").write_text("class A {}", encoding="utf-8")
        os.symlink("A.java", product / "demo/forum-app/Link.java")
        commit(product, "symlink")
        commit_sha = git(product, "rev-parse", "HEAD").stdout.strip()
        snapshot_dir, root = snapshot_with(commit_sha, {"demo/forum-app/A.java": "class A {}"})
        self.addCleanup(snapshot_dir.cleanup)
        with self.assertRaises(source.SourceError) as caught:
            source.refresh(root=root, product=product)
        self.assertEqual(str(caught.exception), "product_entry_not_a_file")

    def test_refresh_refuses_a_product_without_the_pinned_commit(self):
        product_dir, product, _ = product_with("demo/forum-app/A.java", "class A {}")
        snapshot_dir, root = snapshot_with("b" * 40, {"demo/forum-app/A.java": "class A {}"})
        self.addCleanup(product_dir.cleanup)
        self.addCleanup(snapshot_dir.cleanup)
        with self.assertRaises(source.SourceError) as caught:
            source.refresh(root=root, product=product)
        self.assertEqual(str(caught.exception), "product_commit_missing")


if __name__ == "__main__":
    unittest.main()
