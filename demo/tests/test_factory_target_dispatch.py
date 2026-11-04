"""One pinned forum feature through the real dispatch path, without a model call."""
import dataclasses
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.budget import DailyBudget
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

    def worker(self, builder, target=None, checks_command=None, require_circuit=True,
               budget=None, allow_unbudgeted=None, check_sandbox=None):
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
            review_complete=approve if require_circuit else None,
            require_circuit=require_circuit,
            author_model="deepseek-4.1-flash", budget=budget,
            allow_unbudgeted=budget is None if allow_unbudgeted is None else allow_unbudgeted,
            check_sandbox=check_sandbox,
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

    def test_a_lost_isolation_boundary_holds_instead_of_failing_the_build(self):
        from factory.isolation import IsolationError

        def unavailable(*args, **kwargs):
            raise IsolationError("docker boundary unavailable")

        self.store.admit(["013"], "k8", self.catalog)
        result = self.worker(self.builder, require_circuit=False,
                             check_sandbox=unavailable).run_once()
        self.assertEqual(result["result"]["status"], "held")
        self.assertEqual(result["result"]["reason"], "sandbox_unqualified")
        detail = result["result"]["gate"]["results"]["gradle_test"]["detail"]
        self.assertEqual(detail["reason"], "isolation_unqualified")
        build = self.store.board()[0]
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "sandbox_unqualified")
        dispatched = next(e for e in self.store.events(build["build_id"]) if e["event"] == "dispatched")
        self.assertEqual(build["attempt_id"], json.loads(dispatched["detail"])["attempt_id"])

    def test_a_failed_paid_builder_receipt_names_its_own_author(self):
        class FailingBuilder:
            paid = True
            model = "qwen-3.8-flash"
            last_usage = None

            def __call__(self, **kwargs):
                raise RuntimeError("transport down")

        budget = DailyBudget(
            self.root / "ledger.jsonl",
            limits={"aeion-observability": Decimal("15.00"),
                    "aeion-autonomous-forum": Decimal("15.00")},
            today=lambda: "2026-11-02",
        )
        self.store.admit(["013"], "k9", self.catalog)
        self.worker(FailingBuilder(), budget=budget, require_circuit=False).run_once()
        build = self.store.board()[0]
        self.assertEqual(build["status"], FAILED)
        receipt = json.loads(build["receipt"])
        self.assertEqual(receipt["reason"], "builder_error")
        self.assertEqual(receipt["author_model"], "qwen-3.8-flash")
        self.assertFalse(receipt["simulated"])

    def test_a_build_journals_its_zero_cost_reservation_in_the_forum_purse(self):
        budget = DailyBudget(
            self.root / "ledger.jsonl",
            limits={"aeion-observability": Decimal("15.00"),
                    "aeion-autonomous-forum": Decimal("15.00")},
            today=lambda: "2026-11-02",
        )
        self.store.admit(["013"], "k5", self.catalog)
        result = self.worker(self.builder, budget=budget, require_circuit=False).run_once()
        self.assertEqual(result["result"]["status"], "completed")
        self.assertEqual(budget.spent("aeion-autonomous-forum"), Decimal("0.00"))
        self.assertEqual(budget.spent("aeion-observability"), Decimal("0.00"))
        entries = [json.loads(line) for line in
                   (self.root / "ledger.jsonl").read_text().splitlines()]
        self.assertEqual([entry["kind"] for entry in entries], ["reserve", "settle"])
        self.assertEqual({entry["scope"] for entry in entries}, {"aeion-autonomous-forum"})

    def test_a_configured_review_circuit_reserves_each_vote_and_keeps_them_open(self):
        budget = DailyBudget(
            self.root / "ledger.jsonl",
            limits={"aeion-observability": Decimal("15.00"),
                    "aeion-autonomous-forum": Decimal("15.00")},
            today=lambda: "2026-11-02",
        )
        self.store.admit(["013"], "k5b", self.catalog)
        self.worker(self.builder, budget=budget).run_once()
        entries = [json.loads(line) for line in
                   (self.root / "ledger.jsonl").read_text().splitlines()]
        # The build reservation plus one reservation per vote; the fake reviewers report no
        # measured usage, so none of the three may be released as free.
        self.assertEqual([entry["kind"] for entry in entries],
                         ["reserve", "reserve", "reserve"])
        self.assertEqual(budget.spent("aeion-autonomous-forum"), Decimal("0.10"))

    def test_a_worker_without_a_purse_holds_before_any_work(self):
        self.store.admit(["013"], "k6a", self.catalog)
        worker = self.worker(self.builder, allow_unbudgeted=False)
        result = worker.run_once()
        build = self.store.board()[0]
        self.assertEqual(result["result"], {"status": "held", "reason": "budget_unavailable"})
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "budget_unavailable")
        self.assertFalse((self.root / "work").exists())

    def test_an_exhausted_purse_holds_before_a_session_or_builder(self):
        budget = DailyBudget(
            self.root / "ledger.jsonl",
            limits={"aeion-observability": Decimal("15.00"),
                    "aeion-autonomous-forum": Decimal("0.00")},
            today=lambda: "2026-11-02",
        )
        self.store.admit(["013"], "k6", self.catalog)
        worker = self.worker(self.builder, budget=budget)
        worker.config["cost_reservation_usd"] = "0.01"
        result = worker.run_once()
        build = self.store.board()[0]
        self.assertEqual(result["result"], {"status": "held", "reason": "budget_unavailable"})
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "budget_unavailable")
        self.assertFalse((self.root / "work").exists())
        self.assertFalse((self.root / "ledger.jsonl").exists())


    def test_a_target_for_one_feature_never_freezes_another(self):
        other = feature()
        other["id"] = "014"
        other["file"] = "014.md"
        catalog = Catalog({"schema_version": 2, "count": 1, "features": [other]})
        self.store.admit(["014"], "k7", catalog)
        worker = DispatchWorker(
            self.store, catalog, self.specs, self.root / "work", config(),
            target=self.target, builder=self.builder, forge=FakeForge(),
            require_circuit=False, allow_unbudgeted=True,
        )
        result = worker.run_once()
        build = self.store.board()[0]
        self.assertEqual(result["result"], {"status": "held",
                                            "reason": "target_feature_mismatch"})
        self.assertEqual(build["status"], HELD)
        self.assertEqual(build["hold_reason"], "target_feature_mismatch")
        self.assertFalse((self.root / "work").exists())


if __name__ == "__main__":
    unittest.main()
