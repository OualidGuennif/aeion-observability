"""One pinned forum feature through the real dispatch path, without a model call."""
import dataclasses
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.dispatch import DispatchWorker
from factory.manifest import Catalog
from factory.publish import FakeForge
from factory.store import FAILED, HELD, SIMULATED_COMPLETE, Store
from factory.target import load_target


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
    git(source, "config", "user.name", "target-test")
    git(source, "add", "-A")
    git(source, "commit", "-q", "-m", "base")
    sha = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return source, sha


def feature():
    return {
        "id": "013", "title": "Security headers", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum/product/"], "depends_on": [], "file": "013.md",
    }


def config():
    return {"profile": "offline", "mode": "fake", "deadline_ns": 60_000_000_000,
            "step_cap": 100, "context_limit": 250_000, "cost_reservation_usd": "0.00"}


def approve(model, prompt):
    return {"verdict": "approve", "reason": "offline fake reviewer"}


class TargetDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.sha = make_source(self.root)
        (self.root / "brief.md").write_text("# Brief\n")
        (self.root / "contract").mkdir()
        (self.root / "contract/ContractTest.java").write_text("// protected\n")
        self.profile = {
            "schema_version": 1,
            "id": "fixture-013",
            "feature_id": "013",
            "target_repo": "example/forum",
            "base": {"source": "source", "sha": self.sha},
            "allowed_scope_prefix": "demo/forum-app/src/",
            "write_paths": [
                "demo/forum-app/src/main/java/local/aeion/forum/",
                "demo/forum-app/src/test/java/local/aeion/forum/",
            ],
            "brief": "brief.md",
            "protected_check": {
                "id": "gradle_test",
                "command": [sys.executable, "-c",
                            "import pathlib,sys; raise SystemExit(0 if "
                            "pathlib.Path(sys.argv[1]).is_file() else 1)",
                            "{repo}/demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java"],
                "env": {},
                "contract_test": "contract/ContractTest.java",
                "contract_destination": "demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java",
                "timeout_seconds": 30,
            },
        }
        self.target_path = self.root / "target.json"
        self.target_path.write_text(json.dumps(self.profile))
        self.target = load_target(self.target_path, self.root)
        self.catalog = Catalog({"schema_version": 2, "count": 1, "features": [feature()]})
        self.specs = self.root / "specs"
        self.specs.mkdir()
        self.store = Store(self.root / "factory.db")

    def worker(self, builder, target=None, checks_command=None, require_circuit=True):
        target = target or self.target
        if checks_command is not None:
            target = dataclasses.replace(
                target,
                protected_check=dataclasses.replace(target.protected_check,
                                                    command=checks_command),
            )
        return DispatchWorker(
            self.store, self.catalog, self.specs, self.root / "work", config(),
            target=target, builder=builder, forge=FakeForge(),
            review_complete=approve, require_circuit=require_circuit,
            author_model="deepseek-4.1-flash",
        )

    def builder(self, repo, frozen, feature, brief):
        for scope, name in ((frozen.write_scopes[0], "SecurityHeadersFilter.java"),
                            (frozen.write_scopes[1], "SecurityHeadersTest.java")):
            (repo / scope).mkdir(parents=True, exist_ok=True)
            (repo / scope / name).write_text("package local.aeion.forum;\n")
        self.assertEqual(brief.read_text(), "# Brief\n")

    def test_pinned_target_runs_the_real_check_and_records_identity(self):
        self.store.admit(["013"], "k1", self.catalog)
        result = self.worker(self.builder).run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], SIMULATED_COMPLETE)
        receipt = json.loads(build["receipt"])
        self.assertEqual(receipt["build_id"], build["build_id"])
        self.assertEqual(receipt["feature_id"], "013")
        self.assertEqual(receipt["attempt_id"], build["attempt_id"])
        self.assertEqual(receipt["artifact_digest"], receipt["artifact_digest"].lower())
        self.assertEqual(receipt["base_sha"], self.sha)
        self.assertEqual(receipt["gate"]["status"], "passed")
        self.assertEqual(receipt["gate"]["results"]["gradle_test"]["status"], "passed")
        self.assertEqual(receipt["gate"]["results"]["gradle_test"]["detail"]["returncode"], 0)
        self.assertIn("contract_sha256", receipt["gate"]["results"]["gradle_test"]["detail"])
        self.assertEqual(receipt["circuit"]["status"], "approved")
        self.assertEqual(receipt["publisher"]["decision"], "published")
        self.assertEqual(receipt["telemetry"]["status"], "disabled")
        brief = (self.root / "work" / build["build_id"] / "BRIEF.md").read_text()
        self.assertEqual(brief, "# Brief\n")
        task = (self.root / "work" / build["build_id"] / "TASK.md").read_text()
        self.assertIn("BRIEF.md", task)
        self.assertIn("demo/forum-app/src/main/java/local/aeion/forum/", task)

    def test_missing_base_holds_instead_of_inventing_one(self):
        self.store.admit(["013"], "k2", self.catalog)
        missing = dataclasses.replace(self.target, base_source=self.root / "missing")
        result = self.worker(self.builder, target=missing).run_once()
        self.assertEqual(result["result"]["status"], "held")
        self.assertEqual(result["result"]["reason"], "base_unavailable")
        self.assertEqual(self.store.board()[0]["status"], HELD)
        self.assertEqual(self.store.board()[0]["hold_reason"], "base_unavailable")

    def test_builder_failure_never_reaches_the_publisher(self):
        self.store.admit(["013"], "k3", self.catalog)

        def explode(**kwargs):
            raise RuntimeError("boom")

        result = self.worker(explode).run_once()
        build = self.store.board()[0]
        self.assertEqual(build["status"], FAILED)
        receipt = json.loads(build["receipt"])
        self.assertEqual(receipt["reason"], "builder_error")
        self.assertNotIn("publisher", receipt)

    def test_failed_protected_check_never_reaches_the_publisher(self):
        self.store.admit(["013"], "k4", self.catalog)
        command = [sys.executable, "-c", "raise SystemExit(1)", "{repo}"]
        result = self.worker(self.builder, checks_command=command).run_once()
        build = self.store.board()[0]
        self.assertEqual(build["status"], FAILED)
        receipt = json.loads(build["receipt"])
        self.assertEqual(receipt["gate"]["status"], "failed")
        self.assertEqual(receipt["gate"]["results"]["gradle_test"]["status"], "failed")
        self.assertNotIn("publisher", receipt)


if __name__ == "__main__":
    unittest.main()
