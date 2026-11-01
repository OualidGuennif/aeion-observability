import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.analysis import AnalysisError, activate, clone, definition, prepare, state, tools_available

PINNED = {"graphify_revision": "0a8cd4e1", "graphify_version": "0.9.97", "archify_revision": "208acba8"}


def make_repo(root, with_setup=True):
    (root / "tools/architecture").mkdir(parents=True, exist_ok=True)
    (root / "tools/architecture/integrations.json").write_text(json.dumps({
        "graphify": {"revision": "0a8cd4e1", "version": "0.9.97"},
        "archify": {"revision": "208acba8"},
    }))
    if with_setup:
        (root / "tools/architecture/setup").write_text("#!/usr/bin/env python3\n")
    return root


class DefinitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_reads_pinned_revisions(self):
        make_repo(self.root)
        self.assertEqual(definition(self.root), PINNED)

    def test_missing_template_is_reported(self):
        with self.assertRaisesRegex(AnalysisError, "integration_missing:integrations.json"):
            definition(self.root)

    def test_missing_setup_is_reported(self):
        make_repo(self.root, with_setup=False)
        with self.assertRaisesRegex(AnalysisError, "integration_missing:setup"):
            definition(self.root)


class ActivateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fake_installer(self, ok=True):
        calls = []

        def run(argv, **kwargs):
            calls.append(argv)
            if ok:
                (self.root / ".aeion/integrations/graphify-venv/bin").mkdir(parents=True, exist_ok=True)
                (self.root / ".aeion/integrations/graphify-venv/bin/python").write_text("")
                (self.root / ".aeion/integrations/archify/archify/bin").mkdir(parents=True, exist_ok=True)
                (self.root / ".aeion/integrations/archify/archify/bin/archify.mjs").write_text("")
            return SimpleNamespace(returncode=0 if ok else 1, stdout="", stderr="")
        return run, calls

    def test_activation_installs_both_integrations(self):
        make_repo(self.root)
        run, calls = self.fake_installer()
        receipt = activate(self.root, run=run)
        self.assertEqual(receipt["status"], "activated")
        self.assertTrue(receipt["graphify"] and receipt["archify"])
        self.assertEqual(Path(calls[0][1]).resolve(), (self.root / "tools/architecture/setup").resolve())

    def test_second_activation_is_a_noop(self):
        make_repo(self.root)
        run, calls = self.fake_installer()
        activate(self.root, run=run)
        receipt = activate(self.root, run=run)
        self.assertEqual(receipt["status"], "already_active")
        self.assertEqual(len(calls), 1)

    def test_failed_setup_is_refused(self):
        make_repo(self.root)
        run, _ = self.fake_installer(ok=False)
        with self.assertRaisesRegex(AnalysisError, "setup_failed"):
            activate(self.root, run=run)

    def test_incomplete_installation_is_refused(self):
        make_repo(self.root)

        def partial(argv, **kwargs):
            (self.root / ".aeion/integrations/graphify-venv/bin").mkdir(parents=True)
            (self.root / ".aeion/integrations/graphify-venv/bin/python").write_text("")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with self.assertRaisesRegex(AnalysisError, "integration_incomplete:archify"):
            activate(self.root, run=partial)

    def test_state_is_false_before_install(self):
        make_repo(self.root)
        self.assertEqual(state(self.root), {"graphify": False, "archify": False})


class CloneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_clone_uses_a_shallow_branch_clone(self):
        calls = []

        def run(argv, **kwargs):
            calls.append(argv)
            Path(argv[-1]).mkdir(parents=True, exist_ok=True)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        clone("https://example.invalid/o/r", self.root / "clone", branch="develop", run=run)
        self.assertEqual(calls[0][:4], ["git", "clone", "--depth", "1"])
        self.assertIn("--branch", calls[0])
        self.assertIn("develop", calls[0])

    def test_clone_refuses_a_non_empty_destination(self):
        target = self.root / "clone"
        target.mkdir()
        (target / "x").write_text("occupied")

        def run(argv, **kwargs):  # must not be reached
            raise AssertionError("git must not run")
        with self.assertRaisesRegex(AnalysisError, "clone_destination_not_empty"):
            clone("https://example.invalid/o/r", target, run=run)

    def test_prepare_clones_then_activates(self):
        def run(argv, **kwargs):
            if argv[0] == "git":
                dest = Path(argv[-1])
                make_repo(dest)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            dest = self.root / "clone"
            (dest / ".aeion/integrations/graphify-venv/bin").mkdir(parents=True, exist_ok=True)
            (dest / ".aeion/integrations/graphify-venv/bin/python").write_text("")
            (dest / ".aeion/integrations/archify/archify/bin").mkdir(parents=True, exist_ok=True)
            (dest / ".aeion/integrations/archify/archify/bin/archify.mjs").write_text("")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        receipt = prepare("https://example.invalid/o/r", self.root / "clone", branch="develop", run=run)
        self.assertEqual(receipt["status"], "activated")
        self.assertEqual(receipt["branch"], "develop")

    def test_prepare_reports_the_pi_extension(self):
        def run(argv, **kwargs):
            if argv[0] == "git":
                dest = Path(argv[-1])
                make_repo(dest)
                (dest / ".pi/extensions/factory").mkdir(parents=True)
                (dest / ".pi/extensions/factory/index.js").write_text("export default {};\n")
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            dest = self.root / "clone"
            (dest / ".aeion/integrations/graphify-venv/bin").mkdir(parents=True, exist_ok=True)
            (dest / ".aeion/integrations/graphify-venv/bin/python").write_text("")
            (dest / ".aeion/integrations/archify/archify/bin").mkdir(parents=True, exist_ok=True)
            (dest / ".aeion/integrations/archify/archify/bin/archify.mjs").write_text("")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        receipt = prepare("https://example.invalid/o/r", self.root / "clone", run=run)
        self.assertTrue(receipt["pi_extension"]["present"])
        self.assertEqual(receipt["pi_extension"]["required_flag"], "pi -e .pi/extensions/factory/index.js")

    def test_missing_pi_extension_is_reported_not_invented(self):
        def run(argv, **kwargs):
            if argv[0] == "git":
                make_repo(Path(argv[-1]))
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            dest = self.root / "clone"
            (dest / ".aeion/integrations/graphify-venv/bin").mkdir(parents=True, exist_ok=True)
            (dest / ".aeion/integrations/graphify-venv/bin/python").write_text("")
            (dest / ".aeion/integrations/archify/archify/bin").mkdir(parents=True, exist_ok=True)
            (dest / ".aeion/integrations/archify/archify/bin/archify.mjs").write_text("")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        receipt = prepare("https://example.invalid/o/r", self.root / "clone", run=run)
        self.assertFalse(receipt["pi_extension"]["present"])

    def test_host_tools_are_reported(self):
        report = tools_available()
        self.assertEqual(set(report), {"git", "node", "python3"})
        self.assertTrue(report["git"])


if __name__ == "__main__":
    unittest.main()
