#!/usr/bin/env python3
"""Run the real pre-push hook against a disposable repository and a local bare remote."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "pre-push"


class PrePushTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "work"
        remote = Path(self.tmp.name) / "remote.git"
        self.git("init", "-q", "--bare", str(remote), cwd=self.tmp.name)
        self.git("init", "-q", "-b", "main", str(self.root), cwd=self.tmp.name)
        self.git("remote", "add", "origin", str(remote))
        self.commit("initial")
        self.git("push", "-q", "origin", "main")
        self.git("switch", "-q", "-c", "develop")

    def git(self, *args, cwd=None):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                              cwd=cwd or self.root, capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, message):
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def push(self, remote_ref, sha):
        line = f"refs/heads/x {sha} {remote_ref} {'0' * 40}\n"
        return subprocess.run([sys.executable, str(HOOK), "origin", "url"], cwd=self.root, input=line,
                              capture_output=True, text=True, timeout=10)

    def review(self, sha, text):
        folder = self.root / ".aeion/reviews"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{sha}.md").write_text(text)

    def test_develop_needs_an_ok_review_of_the_exact_commit(self):
        sha = self.commit("work")
        self.assertEqual(self.push("refs/heads/develop", sha).returncode, 1)
        self.review(sha, "Review: NOT OK\n- a finding\n")
        self.assertEqual(self.push("refs/heads/develop", sha).returncode, 1)
        self.review(sha, "Review: OK\n")
        self.assertEqual(self.push("refs/heads/develop", sha).returncode, 0)
        # A review of an older commit does not cover new work.
        newer = self.commit("more work")
        self.assertIn("no 'Review: OK'", self.push("refs/heads/develop", newer).stderr)

    def test_main_is_refused_and_develop_may_catch_up_with_it(self):
        sha = self.git("rev-parse", "HEAD")
        self.assertIn("release pull request", self.push("refs/heads/main", sha).stderr)
        # After a release, develop fast-forwards to the merged main; that commit was reviewed in the release.
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.push("refs/heads/develop", sha).returncode, 0)

    def test_deletions_tags_and_task_branches_pass(self):
        sha = self.commit("work")
        self.assertEqual(self.push("refs/heads/develop", "0" * 40).returncode, 0)
        self.assertEqual(self.push("refs/tags/v1.3.0", sha).returncode, 0)
        self.assertEqual(self.push("refs/heads/task/x", sha).returncode, 0)

    def test_local_mode_pushes_main_without_the_team_flow(self):
        sha = self.commit("play")
        self.git("config", "aeion.mode", "local")
        self.assertEqual(self.push("refs/heads/main", sha).returncode, 0)
        self.git("config", "--unset", "aeion.mode")
        self.assertEqual(self.push("refs/heads/main", sha).returncode, 1)

    def test_a_symlinked_review_is_not_a_verdict(self):
        sha = self.commit("work")
        target = Path(self.tmp.name) / "elsewhere.md"
        target.write_text("Review: OK\n")
        (self.root / ".aeion/reviews").mkdir(parents=True)
        (self.root / ".aeion/reviews" / f"{sha}.md").symlink_to(target)
        self.assertEqual(self.push("refs/heads/develop", sha).returncode, 1)


if __name__ == "__main__":
    unittest.main()
