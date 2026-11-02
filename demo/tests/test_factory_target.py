"""Pinned target profiles: identity is proven before a build touches a tree."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.target import TargetError, load_target


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          check=check)


def make_source(root):
    source = root / "source"
    (source / "demo/forum-app/src/main/java/local/aeion/forum").mkdir(parents=True)
    (source / "demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java").write_text(
        "package local.aeion.forum;\n")
    git(source, "init", "-q")
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "target-test")
    git(source, "add", "-A")
    git(source, "commit", "-q", "-m", "base")
    return source, git(source, "rev-parse", "HEAD").stdout.strip()


def profile_data(sha, destination="demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java"):
    return {
        "schema_version": 1,
        "id": "fixture-013",
        "feature_id": "013",
        "target_repo": "example/forum",
        "base": {"source": "source", "sha": sha},
        "allowed_scope_prefix": "demo/forum-app/src/",
        "write_paths": [
            "demo/forum-app/src/main/java/local/aeion/forum/",
            "demo/forum-app/src/test/java/local/aeion/forum/",
        ],
        "brief": "brief.md",
        "protected_check": {
            "id": "gradle_test",
            "command": [sys.executable, "-c", "raise SystemExit(0)", "{repo}"],
            "env": {},
            "contract_test": "contract/ContractTest.java",
            "contract_destination": destination,
            "timeout_seconds": 30,
        },
    }


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.sha = make_source(self.root)
        (self.root / "brief.md").write_text("# Brief\n")
        (self.root / "contract").mkdir()
        (self.root / "contract/ContractTest.java").write_text("// contract\n")

    def write(self, data):
        path = self.root / "target.json"
        path.write_text(json.dumps(data))
        return path

    def load(self, data=None):
        return load_target(self.write(profile_data(self.sha) if data is None else data), self.root)

    def test_loads_and_materializes_the_pinned_base(self):
        target = self.load()
        self.assertEqual(target.feature_id, "013")
        self.assertEqual(target.base_sha, self.sha)
        self.assertEqual(target.write_paths[0], "demo/forum-app/src/main/java/local/aeion/forum/")
        destination = self.root / "work/repo"
        self.assertEqual(target.materialize(destination), self.sha)
        self.assertEqual(git(destination, "rev-parse", "HEAD").stdout.strip(), self.sha)
        self.assertTrue((destination / "demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java").is_file())
        self.assertEqual(git(destination, "status", "--porcelain").stdout, "")

    def test_materialize_refuses_an_existing_destination(self):
        target = self.load()
        destination = self.root / "work/repo"
        target.materialize(destination)
        with self.assertRaisesRegex(TargetError, "destination_exists"):
            target.materialize(destination)

    def test_rejects_a_sha_that_is_not_a_commit(self):
        data = profile_data(self.sha)
        data["base"]["sha"] = "0" * 40
        with self.assertRaisesRegex(TargetError, "base_commit_missing"):
            self.load(data)

    def test_rejects_a_scope_outside_the_target_prefix(self):
        data = profile_data(self.sha)
        data["write_paths"] = ["demo/forum/product/"]
        with self.assertRaisesRegex(TargetError, "scope_outside_target"):
            self.load(data)

    def test_rejects_a_contract_inside_the_candidate_scope(self):
        data = profile_data(self.sha)
        candidate_contract = self.source / "demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java"
        candidate_contract.parent.mkdir(parents=True)
        candidate_contract.write_text("// candidate\n")
        data["protected_check"]["contract_test"] = str(candidate_contract.relative_to(self.root))
        with self.assertRaisesRegex(TargetError, "contract_test_in_candidate_scope"):
            self.load(data)

    def test_rejects_a_tracked_contract_destination(self):
        destination = "demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java"
        tracked = self.source / destination
        tracked.parent.mkdir(parents=True)
        tracked.write_text("// already tracked\n")
        git(self.source, "add", "-A")
        git(self.source, "commit", "-q", "-m", "tracked contract slot")
        data = profile_data(self.sha)
        data["base"]["sha"] = git(self.source, "rev-parse", "HEAD").stdout.strip()
        with self.assertRaisesRegex(TargetError, "contract_destination_tracked"):
            self.load(data)

    def test_rejects_a_missing_brief(self):
        (self.root / "brief.md").unlink()
        with self.assertRaisesRegex(TargetError, "brief_missing"):
            self.load()

    def test_rejects_an_invalid_timeout(self):
        data = profile_data(self.sha)
        data["protected_check"]["timeout_seconds"] = 0
        with self.assertRaisesRegex(TargetError, "invalid_check_timeout"):
            self.load(data)


if __name__ == "__main__":
    unittest.main()
