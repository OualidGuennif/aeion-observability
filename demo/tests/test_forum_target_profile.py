"""The real pinned profile: one feature, the runnable app, and a check outside the diff."""
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import load_manifest
from factory.target import load_target

REPO = Path(__file__).resolve().parents[2]
PROFILE = REPO / "demo/forum/targets/forum-app-013.json"


class ForumTargetProfileTests(unittest.TestCase):
    def setUp(self):
        self.target = load_target(PROFILE, REPO)
        self.product = self.target.base_source
        self.catalog = load_manifest(REPO / "demo/forum/features/MANIFEST.json")

    def test_it_names_catalog_feature_013_and_the_autonomous_product_repo(self):
        self.assertEqual(self.target.feature_id, "013")
        self.assertEqual(self.target.target_repo, "OualidGuennif/aeion-autonomous-forum")
        self.assertEqual(self.catalog.by_id["013"]["title"], "Security headers and CSP")

    def test_the_base_is_an_ancestor_with_the_runnable_app(self):
        ancestor = subprocess.run(
            ["git", "-C", str(self.product), "merge-base", "--is-ancestor",
             self.target.base_sha, "HEAD"], capture_output=True, text=True)
        self.assertEqual(ancestor.returncode, 0)
        for path in ("demo/forum-app/build.gradle",
                     "demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java",
                     "demo/forum-app/src/test/java/local/aeion/forum/QuarkusTestDatabase.java"):
            shown = subprocess.run(
                ["git", "-C", str(self.product), "cat-file", "-e",
                 f"{self.target.base_sha}:{path}"], capture_output=True, text=True)
            self.assertEqual(shown.returncode, 0, path)

    def test_the_scopes_are_the_quarkus_source_and_test_trees(self):
        self.assertEqual(self.target.write_paths, [
            "demo/forum-app/src/main/java/local/aeion/forum/",
            "demo/forum-app/src/test/java/local/aeion/forum/",
        ])
        self.assertTrue(self.target.brief.read_text().startswith("# 013"))

    def test_the_contract_is_outside_the_scopes_and_untracked_at_the_base(self):
        for scope in self.target.write_paths:
            self.assertFalse(self.target.protected_check.contract_test.is_relative_to(
                self.product / scope))
        shown = subprocess.run(
            ["git", "-C", str(self.product), "cat-file", "-e",
             f"{self.target.base_sha}:{self.target.protected_check.contract_destination}"],
            capture_output=True, text=True)
        self.assertNotEqual(shown.returncode, 0)

    def test_the_check_runs_the_offline_gradle_suite(self):
        command = self.target.protected_check.command
        self.assertIn("test", command)
        self.assertIn("--offline", command)
        self.assertIn("--no-daemon", command)
        self.assertTrue(any("{repo}/demo/forum-app" in part for part in command))
        self.assertIn("GRADLE_USER_HOME", self.target.protected_check.env)


if __name__ == "__main__":
    unittest.main()
