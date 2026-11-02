"""The isolated check boundary: path translation and fail-closed wiring (no container run)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.isolation import DockerCheckRunner, IsolationError


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.controller = Path(self.tmp.name)
        self.tools = self.controller / "demo/.local/tools"
        self.cache = self.controller / "demo/.local/gradle-home/caches"
        self.tools.mkdir(parents=True)
        self.cache.mkdir(parents=True)
        self.repo = self.controller / "work/build/repo"
        self.runner = DockerCheckRunner(self.controller)

    def test_repository_and_toolchain_paths_map_to_mounts(self):
        translated = self.runner.translate(
            str(self.tools / "gradle-9.8.2/bin/gradle"), self.repo)
        self.assertEqual(translated, "/tools/gradle-9.8.2/bin/gradle")
        translated = self.runner.translate(str(self.repo / "demo/forum-app"), self.repo)
        self.assertEqual(translated, "/workspace/demo/forum-app")

    def test_ordinary_arguments_pass_through(self):
        self.assertEqual(self.runner.translate("test", self.repo), "test")
        self.assertEqual(self.runner.translate("--offline", self.repo), "--offline")

    def test_another_controller_path_is_refused(self):
        with self.assertRaises(IsolationError):
            self.runner.translate(str(self.controller / "demo/.env"), self.repo)

    def test_a_repository_sibling_is_not_rewritten(self):
        sibling = Path("/tmp/aeion-sibling-repo/file")
        self.assertEqual(self.runner.translate(str(sibling), self.repo), str(sibling))

    def test_execution_runs_the_qualified_digest_not_the_mutable_tag(self):
        digest = "sha256:" + "a" * 64
        self.runner._qualification = {"status": "qualified", "image": self.runner.image,
                                      "image_id": digest}
        calls = []

        def fake_run(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "", "")

        with mock.patch("factory.isolation.subprocess.run", side_effect=fake_run):
            self.runner(["true"], cwd=self.repo)
        self.assertIn(digest, calls[0])
        self.assertNotIn(self.runner.image, calls[0])


if __name__ == "__main__":
    unittest.main()
