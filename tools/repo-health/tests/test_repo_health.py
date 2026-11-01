#!/usr/bin/env python3
"""Run the real health check in disposable repositories and plain folders."""
import importlib.util
import shutil
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "repo-health"
FILES = Path(__file__).resolve().parents[3] / ".claude/hooks/project_files.py"


class RepoHealthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.tool = self.root / "tools/repo-health/repo-health"
        self.tool.parent.mkdir(parents=True)
        shutil.copy(TOOL, self.tool)
        (self.root / ".claude/hooks").mkdir(parents=True)
        shutil.copy(FILES, self.root / ".claude/hooks/project_files.py")

    def check_health(self, *args):
        return subprocess.run([sys.executable, str(self.tool), *args], cwd=self.root,
                              capture_output=True, text=True, timeout=10)

    def test_plain_folder_is_walked_without_git(self):
        # Many users have no git: the caps still apply to the files on disk, dependencies excluded.
        (self.root / "big.py").write_text("value = 1\n" * 1501)
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules/huge.js").write_text("x\n" * 5000)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("big.py", result.stdout)
        self.assertNotIn("huge.js", result.stdout)

    def test_desktop_files_and_build_output_are_not_walked(self):
        (self.root / ".DS_Store").write_bytes(b"\0" * 10)
        (self.root / "dist").mkdir()
        (self.root / "dist/bundle.js").write_text("x\n" * 5000)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_only_identified_passive_pool_is_exempt_from_authored_source_caps(self):
        (self.root / "skills").mkdir()
        (self.root / "skills/vendor.py").write_text("value = 1\n" * 1501)
        self.assertEqual(self.check_health().returncode, 1)
        (self.root / "skills/catalog.json").write_text(json.dumps({"generator": "aeion-skill-files-v2"}))
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["passive_pool_source_files_excluded"], 1)
        (self.root / "tools/skills").mkdir()
        (self.root / "tools/skills/pool.py").write_text("value = 1\n" * 1501)
        result = self.check_health()
        self.assertEqual(result.returncode, 1)
        self.assertIn("tools/skills/pool.py", result.stderr)

    def test_build_named_source_below_the_root_is_walked(self):
        # Only the root's build output is skipped; a source folder named build deeper is the project's code.
        (self.root / "src/build").mkdir(parents=True)
        (self.root / "src/build/big.py").write_text("value = 1\n" * 1501)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("src/build/big.py", result.stdout)

    def test_plain_walk_honours_simple_gitignore_rules_below_their_folder(self):
        # Fresh writes app/_fresh, which app/.gitignore excludes; git would not list it either.
        (self.root / "app/_fresh/server").mkdir(parents=True)
        (self.root / "app/_fresh/server/entry.mjs").write_text("x\n" * 5000)
        (self.root / "app/debug.log").write_text("x\n" * 5000)
        (self.root / "app/.gitignore").write_text("# build\n_fresh/\n*.log\n!keep.log\n/anchored\nsub/path\n")
        (self.root / "other").mkdir()
        (self.root / "other/_fresh").write_text("value = 1\n" * 1501)
        result = self.check_health("--json")
        self.assertNotIn("entry.mjs", result.stdout + result.stderr)
        self.assertNotIn("debug.log", result.stdout + result.stderr)
        # The rule lives in app/ only, and a directory rule never hides a file.
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        spec = importlib.util.spec_from_file_location("project_files", self.root / ".claude/hooks/project_files.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        listed = module.project_files(self.root)
        self.assertIn("other/_fresh", listed)
        self.assertNotIn("app/_fresh/server/entry.mjs", listed)
        self.assertNotIn("app/debug.log", listed)
        self.assertEqual(module.ignore_rules(self.root / "app"), [("_fresh", True), ("*.log", False)])

    def test_repository_reached_through_another_letter_case_stays_a_repository(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        swapped = Path(str(self.tool).swapcase())
        if not swapped.exists():
            self.skipTest("case-sensitive file system")
        result = subprocess.run([sys.executable, str(swapped)], cwd=str(self.root).swapcase(),
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_folder_nested_in_another_repository_is_walked(self):
        # A plain project unpacked inside a parent repository is not tracked there: git would list nothing.
        parent = Path(self.directory.name)
        subprocess.run(["git", "init", "-q", str(parent)], check=True)
        nested = parent / "proj"
        (nested / "tools/repo-health").mkdir(parents=True)
        (nested / ".claude/hooks").mkdir(parents=True)
        shutil.copy(TOOL, nested / "tools/repo-health/repo-health")
        shutil.copy(FILES, nested / ".claude/hooks/project_files.py")
        (nested / "big.py").write_text("value = 1\n" * 1501)
        result = subprocess.run([sys.executable, str(nested / "tools/repo-health/repo-health"), "--json"], cwd=nested,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("big.py", result.stdout)

    def test_broken_repository_still_fails(self):
        (self.root / ".git").write_text("gitdir: /nonexistent\n")
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_valid_repository_produces_a_scorecard(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        result = self.check_health()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repo-health:", result.stdout)

    def test_accented_source_is_checked_against_the_size_cap(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        source = self.root / "café.py"
        source.write_text("value = 1\n" * 1501)
        subprocess.run(["git", "add", "café.py"], cwd=self.root, check=True)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        card = json.loads(result.stdout)
        self.assertEqual(card["files_over_1500_lines"], ["café.py"])
        self.assertEqual(card["source_files_checked"], 1)
        self.assertIn(".py", card["source_suffixes"])


    def test_extensionless_script_is_checked_and_plain_text_is_not(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "refresh").write_text("#!/usr/bin/env python3\n" + "value = 1\n" * 1501)
        (self.root / "LICENSE").write_text("text\n" * 1501)
        subprocess.run(["git", "add", "refresh", "LICENSE"], cwd=self.root, check=True)
        result = self.check_health("--json")
        self.assertEqual(result.returncode, 1)
        card = json.loads(result.stdout)
        self.assertEqual(card["files_over_1500_lines"], ["refresh"])
        self.assertEqual(card["source_files_checked"], 1)


if __name__ == "__main__":
    unittest.main()
