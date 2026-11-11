"""The browser-facing app must use the configured execution, never a silent fake fallback."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import settings  # noqa: F401
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
        protocol = mock.patch('factory.execution.protocol_hash',return_value='a'*64)
        protocol.start();self.addCleanup(protocol.stop)

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

    def test_live_without_a_provider_credential_holds(self):
        self.profile()
        with mock.patch("factory.execution.provider_available", return_value=False):
            execution = resolve(self.root, "live")
        self.assertEqual(execution["mode"], "live")
        self.assertEqual(execution["hold_reason"], "provider_unconfigured")
        self.assertNotIn("builder", execution)

    def test_unqualified_flue_keeps_only_the_guarded_flue_runtime(self):
        self.profile()
        with mock.patch('factory.execution.provider_available', return_value=True), \
                mock.patch('factory.execution.flue_factory_ready', return_value=False):
            execution = resolve(self.root, 'live')
        self.assertEqual(execution['hold_reason'], 'flue_factory_unqualified')
        self.assertEqual(execution['builder'].engine, 'flue-pi')
        self.assertTrue(callable(execution['admission_check']))
        with mock.patch('factory.execution.flue_factory_ready', return_value=False):
            self.assertIs(execution['admission_check'](), False)
        with mock.patch('factory.execution.flue_factory_ready', return_value=True):
            self.assertIs(execution['admission_check'](), True)

    def test_live_resolves_a_paid_builder_isolated_checker_and_reservation(self):
        self.profile()
        clean = {k: v for k, v in os.environ.items() if not k.startswith("AEION_") or not k.endswith("_USD")}
        with mock.patch("factory.execution.provider_available", return_value=True), \
                mock.patch("factory.execution.flue_factory_ready", return_value=True), \
                mock.patch.dict("os.environ", clean, clear=True):
            execution = resolve(self.root, "live")
        self.assertEqual(execution["mode"], "live")
        self.assertNotIn("hold_reason", execution)
        self.assertTrue(execution["builder"].paid)
        self.assertIsNotNone(execution["check_sandbox"])
        self.assertEqual(execution["cost_reservation_usd"], "50.00")
        self.assertEqual(execution["review_complete"].cost_limit, "1.00")
        self.assertIs(execution['builder'].check_sandbox,execution['check_sandbox'])
        self.assertIs(execution['preparer'].checker,execution['check_sandbox'])
        with mock.patch("factory.execution.provider_available", return_value=True), \
                mock.patch("factory.execution.flue_factory_ready", return_value=True), \
                mock.patch.dict("os.environ", {**clean, "AEION_AUTHOR_MAX_USD": "50"}, clear=True):
            self.assertEqual(resolve(self.root, "live")["cost_reservation_usd"], "50.00")

    def test_live_bounds_follow_the_budget_file_and_an_invalid_file_holds(self):
        self.profile()
        conf = self.root / "budget.conf"
        clean = {k: v for k, v in os.environ.items() if not k.startswith("AEION_") or not k.endswith("_USD")}
        with mock.patch("factory.execution.provider_available", return_value=True), \
                mock.patch("factory.execution.flue_factory_ready", return_value=True), \
                mock.patch("factory.budget.CONFIG_PATH", conf), \
                mock.patch.dict("os.environ", clean, clear=True):
            conf.write_text("AUTHOR_MAX_USD=5.00\nREVIEW_MAX_USD=0.40\n")
            execution = resolve(self.root, "live")
            self.assertEqual(execution["cost_reservation_usd"], "5.00")
            self.assertEqual(execution["review_complete"].cost_limit, "0.40")
            conf.write_text("AUTHOR_MAX_USD=50.01\n")
            execution = resolve(self.root, "live")
        self.assertEqual(execution["hold_reason"], "budget_config_invalid")
        self.assertNotIn("builder", execution)

    def test_new_disk_qualification_cannot_authorize_a_stale_loaded_runtime(self):
        self.profile()
        with mock.patch('factory.execution.provider_available',return_value=True), \
                mock.patch('factory.execution.flue_factory_ready',return_value=True), \
                mock.patch('factory.execution.protocol_hash',return_value='a'*64) as protocol:
            execution=resolve(self.root,'live')
            self.assertTrue(execution['admission_check']())
            protocol.return_value='b'*64
            self.assertFalse(execution['admission_check']())

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
        self.assertIsNone(view["execution"]["author_window_seconds"])

    def test_the_catalog_reports_the_configured_author_window(self):
        from types import SimpleNamespace
        builder = SimpleNamespace(timeout_seconds=10800, paid=False)
        view = self.app({"mode": "offline", "hold_reason": "execution_unavailable", "builder": builder}) \
            .catalog_view(None)[1]
        self.assertEqual(view["execution"]["author_window_seconds"], 10800)


if __name__ == "__main__":
    unittest.main()
