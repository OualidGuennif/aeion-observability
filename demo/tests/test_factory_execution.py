"""The browser-facing app must use the configured execution, never a silent fake fallback."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.api import FactoryApp
from factory.budget import DailyBudget
from factory.execution import offline_builder, resolve


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


def make_source(root):
    source = root / "source"
    (source / "demo/forum-app/src/main/java/local/aeion/forum").mkdir(parents=True)
    (source / "demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java").write_text(
        "package local.aeion.forum;\n")
    (source / ".gitignore").write_text("build/\n.gradle/\n")
    git(source, "init", "-q")
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "execution-test")
    git(source, "add", "-A")
    git(source, "commit", "-q", "-m", "base")
    sha = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return source, sha


def feature(feature_id="013"):
    return {
        "id": feature_id, "title": "Security headers", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum-app/src/main/java/local/aeion/forum/"],
        "depends_on": [], "file": f"{feature_id}.md",
    }


def write_profile(root):
    source, sha = make_source(root)
    (root / "brief.md").write_text("# Feature 013 — Security headers and CSP\n")
    (root / "contract").mkdir()
    (root / "contract/ContractTest.java").write_text("// protected\n")
    data = {
        "schema_version": 1, "id": "fixture-013", "feature_id": "013",
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
            "env": {}, "contract_test": "contract/ContractTest.java",
            "contract_destination": "demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java",
            "timeout_seconds": 30,
        },
    }
    path = root / "demo/forum/targets/forum-app-013.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data))
    return source, sha


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def profile(self):
        self.source, self.sha = write_profile(self.root)

    def test_simulator_is_explicit_and_has_no_target(self):
        execution = resolve(self.root, "simulator")
        self.assertEqual(execution, {"mode": "simulator"})

    def test_an_unknown_mode_holds_instead_of_guessing(self):
        execution = resolve(self.root, "surprise")
        self.assertEqual(execution["mode"], "surprise")
        self.assertEqual(execution["hold_reason"], "execution_mode_unknown")
        self.assertNotIn("builder", execution)

    def test_offline_without_a_profile_holds_and_never_simulates(self):
        execution = resolve(self.root, "offline")
        self.assertEqual(execution["mode"], "offline")
        self.assertEqual(execution["hold_reason"], "execution_unavailable")
        self.assertNotIn("target", execution)
        self.assertNotIn("builder", execution)

    def test_offline_with_a_pinned_profile_returns_target_builder_and_telemetry(self):
        self.profile()
        execution = resolve(self.root, "offline")
        self.assertEqual(execution["mode"], "offline")
        self.assertNotIn("hold_reason", execution)
        self.assertEqual(execution["target"].feature_id, "013")
        self.assertIs(execution["builder"], offline_builder)
        self.assertIsNotNone(execution["check_sandbox"])
        self.assertIsNotNone(execution["telemetry"])

    def test_the_offline_builder_writes_both_scopes(self):
        repo = self.root / "repo"
        frozen = SimpleNamespace(write_scopes=["main/", "test/"])
        brief = self.root / "brief-013.md"
        brief.write_text("# Feature 013 — Security headers and CSP\n")
        offline_builder(repo=repo, frozen=frozen, feature=feature(), brief=brief)
        self.assertTrue((repo / "main/SecurityHeadersFilter.java").is_file())
        self.assertTrue((repo / "test/SecurityHeadersTest.java").is_file())

    def test_the_offline_builder_refuses_another_feature_or_brief(self):
        repo = self.root / "repo"
        frozen = SimpleNamespace(write_scopes=["main/", "test/"])
        brief = self.root / "brief.md"
        brief.write_text("# Something else\n")
        with self.assertRaisesRegex(RuntimeError, "brief_does_not_name_this_feature"):
            offline_builder(repo=repo, frozen=frozen, feature=feature("014"), brief=brief)


class AppWiringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps(
            {"schema_version": 2, "count": 1, "features": [feature()]}))
        self.specs = self.root / "specs"
        self.specs.mkdir()
        self.budget = DailyBudget(self.root / "ledger.jsonl")

    def app(self, execution=None):
        return FactoryApp(self.manifest, self.root / "state", spec_dir=self.specs,
                          budget=self.budget, execution=execution)

    def test_the_default_is_the_explicit_simulator(self):
        view = self.app().catalog_view(None)[1]
        self.assertEqual(view["execution"]["mode"], "simulator")
        self.assertIsNone(view["execution"]["hold_reason"])
        self.assertIsNone(view["execution"]["target_feature"])

    def test_an_unavailable_offline_execution_holds_every_build(self):
        app = self.app({"mode": "offline", "hold_reason": "execution_unavailable"})
        app.store.admit(["013"], "k1", app.catalog)
        app.tick()
        build = app.store.board()[0]
        self.assertEqual(build["status"], "held")
        self.assertEqual(build["hold_reason"], "execution_unavailable")
        self.assertFalse((self.root / "state/work").exists())

    def test_offline_execution_runs_the_real_builder_and_check(self):
        write_profile(self.root)
        execution = resolve(self.root, "offline")
        execution["telemetry"] = None
        # The fixture profile runs a Python command, not the pinned Gradle image.
        execution["check_sandbox"] = None
        app = self.app(execution)
        app.store.admit(["013"], "k2", app.catalog)
        app.tick()
        build = app.store.board()[0]
        receipt = json.loads(build["receipt"] or "{}")
        self.assertEqual(build["status"], "simulated_complete")
        self.assertEqual(receipt["gate"]["status"], "passed")
        self.assertTrue(receipt["simulated"])
        work = self.root / "state/work" / build["build_id"] / "repo"
        self.assertTrue((work / "demo/forum-app/src/main/java/local/aeion/forum/"
                               "SecurityHeadersFilter.java").is_file())
        self.assertFalse((work / "demo/forum/product/013-impl.md").exists())

    def test_the_catalog_reports_the_hold_and_the_live_reason(self):
        view = self.app({"mode": "offline", "hold_reason": "execution_unavailable"}) \
            .catalog_view(None)[1]
        self.assertEqual(view["execution"]["mode"], "offline")
        self.assertEqual(view["execution"]["hold_reason"], "execution_unavailable")
        self.assertEqual(view["execution"]["live_hold_reason"], "live_builder_unqualified")


if __name__ == "__main__":
    unittest.main()
