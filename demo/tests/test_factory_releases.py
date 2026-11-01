"""The release service: staging isolation, promotion, dwells, gate, rollback and flags."""
import json
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploy.cache import FileCache
from deploy.playground import Playground
from factory import canary, release
from factory.releases import ReleaseError, ReleaseService
from factory.store import Store

FEATURES = [{"id": "001", "title": "App skeleton", "digest": "a" * 64},
            {"id": "002", "title": "Settings", "digest": "b" * 64}]
HOUR_NS = 3600 * 1_000_000_000


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "factory.db")
        self.playground = Playground(FileCache(self.root / "cache"), seed="staged", percent=0).start()
        self.addCleanup(self.playground.stop)
        self.now = 1_700_000_000_000_000_000
        self.service = ReleaseService(self.store, self.playground, self.root / "releases",
                                      clock=lambda: self.now, sample_interval_seconds=0)

    # ------------------------------------------------------------------ helpers
    def http(self, port, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}") as response:
            return response.status, response.read()

    def warm(self, count=4, tolerate=False):
        for _ in range(count):
            request = urllib.request.Request(f"http://127.0.0.1:{self.playground.port}/api/threads",
                                             headers={"X-Client": "agent-1"})
            try:
                with urllib.request.urlopen(request) as response:
                    response.read()
            except urllib.error.HTTPError as exc:
                exc.close()
                if not tolerate:
                    raise

    def samples(self, count=4, **overrides):
        base = {"requests": 500, "errors_5xx": 0, "error_rate": 0.001, "p95_ms": 90.0,
                "cache_hit_rate": 0.8}
        base.update(overrides)
        return [dict(base) for _ in range(count)]

    # ------------------------------------------------------------------ staging
    def test_staging_serves_the_release_before_any_of_production_does(self):
        record = self.service.stage(FEATURES, now=self.now)
        self.assertEqual(record["state"], release.STATE_STAGED)
        status, body = self.http(self.playground.staging_port, "/__release")
        self.assertEqual(status, 200)
        self.assertIn(record["release_id"].encode(), body)
        self.assertEqual(self.playground.stats()["percent"], 0)

    def test_the_same_features_stage_one_release(self):
        first = self.service.stage(FEATURES, now=self.now)
        second = self.service.stage(FEATURES, now=self.now + 1)
        self.assertEqual(first["release_id"], second["release_id"])
        self.assertEqual(self.store.meta_get("release:current"), first["release_id"])

    def test_a_staged_release_is_not_reachable_on_the_production_balancer(self):
        self.service.stage(FEATURES, now=self.now)
        self.warm(1, tolerate=True)
        stats = self.playground.stats()
        self.assertEqual(stats["percent"], 0)
        self.assertEqual(stats["release"], None)

    # ------------------------------------------------------------------ promotion
    def test_validate_starts_the_first_step_at_25_percent(self):
        self.service.stage(FEATURES, now=self.now)
        record = self.service.validate(now=self.now + 5)
        self.assertEqual(record["state"], release.STATE_CANARY)
        self.assertEqual(record["percent"], 25)
        self.assertEqual(self.playground.stats()["percent"], 25)
        self.assertEqual(self.playground.stats()["release"], record["release_id"])

    def test_validate_twice_is_refused(self):
        self.service.stage(FEATURES, now=self.now)
        self.service.validate(now=self.now)
        with self.assertRaisesRegex(ReleaseError, "cannot_validate_from:canary"):
            self.service.validate(now=self.now)

    def test_advance_waits_for_the_dwell(self):
        self.service.stage(FEATURES, now=self.now)
        self.service.validate(now=self.now)
        self.service._save_samples(self.service.current()["release_id"], self.samples())
        with self.assertRaisesRegex(ReleaseError, "dwell_not_finished"):
            self.service.advance(now=self.now + 60 * 1_000_000_000)

    def test_advance_needs_a_positive_gate(self):
        self.service.stage(FEATURES, now=self.now)
        self.service.validate(now=self.now)
        with self.assertRaisesRegex(ReleaseError, "gate_blocks_advance:insufficient"):
            self.service.advance(now=self.now + 7 * HOUR_NS)

    def test_advance_widens_the_rollout_when_the_evidence_is_good(self):
        self.service.stage(FEATURES, now=self.now)
        record = self.service.validate(now=self.now)
        self.service._save_samples(record["release_id"], self.samples())
        record = self.service.advance(now=self.now + 7 * HOUR_NS)
        self.assertEqual(record["percent"], 50)
        self.assertEqual(self.playground.stats()["percent"], 50)
        record = self.service.advance(now=self.now + 20 * HOUR_NS)
        self.assertEqual(record["state"], release.STATE_RELEASED)
        self.assertEqual(record["percent"], 100)

    def test_immediate_full_deploy_reaches_100_and_says_so(self):
        self.service.stage(FEATURES, now=self.now)
        record = self.service.deploy_now(now=self.now + 2)
        self.assertEqual(record["state"], release.STATE_RELEASED)
        self.assertEqual(record["percent"], 100)
        self.assertEqual(self.playground.stats()["percent"], 100)
        self.assertEqual(record["history"][-1]["event"], "immediate_full_deploy")

    # ------------------------------------------------------------------ monitoring
    def test_a_five_xx_rolls_back_on_the_same_tick(self):
        self.service.stage(FEATURES, now=self.now)
        record = self.service.validate(now=self.now)
        self.service._save_samples(record["release_id"], self.samples(errors_5xx=2, error_rate=0.004))
        outcome = self.service.tick(now=self.now + 300 * 1_000_000_000)
        self.assertEqual(outcome["event"], "rolled_back")
        self.assertEqual(self.service.current()["state"], release.STATE_ROLLED_BACK)
        self.assertEqual(self.playground.stats()["percent"], 0)

    def test_a_latency_breach_holds_without_serving_more(self):
        self.service.stage(FEATURES, now=self.now)
        record = self.service.validate(now=self.now)
        self.service._save_samples(record["release_id"], self.samples(p95_ms=900.0))
        outcome = self.service.tick(now=self.now + 300 * 1_000_000_000)
        self.assertEqual(outcome["event"], "held")
        self.assertEqual(self.service.current()["percent"], 25)
        self.assertEqual(self.playground.stats()["percent"], 25)

    def test_resume_needs_the_gate_to_agree(self):
        self.service.stage(FEATURES, now=self.now)
        record = self.service.validate(now=self.now)
        self.service._save_samples(record["release_id"], self.samples(p95_ms=900.0))
        self.service.tick(now=self.now + 1)
        with self.assertRaisesRegex(ReleaseError, "gate_blocks_resume:hold"):
            self.service.resume(now=self.now + 2)
        self.service._save_samples(record["release_id"], self.samples())
        self.assertEqual(self.service.resume(now=self.now + 3)["state"], release.STATE_CANARY)

    def test_a_tick_records_what_the_balancer_served(self):
        self.service.stage(FEATURES, now=self.now)
        self.service.validate(now=self.now)
        self.warm(6)
        self.service.tick(now=self.now + 300 * 1_000_000_000)
        samples = json.loads(self.store.meta_get("samples:" + self.service.current()["release_id"]))
        self.assertEqual(len(samples), 1)
        self.assertGreater(samples[0]["requests"], 0)

    def test_the_operator_rollback_is_recorded_with_its_reason(self):
        self.service.stage(FEATURES, now=self.now)
        self.service.validate(now=self.now)
        record = self.service.rollback(reason="owner_decision", now=self.now + 9)
        self.assertEqual(record["state"], release.STATE_ROLLED_BACK)
        self.assertEqual(record["rollback_reason"], "owner_decision")
        self.assertEqual(self.playground.stats()["percent"], 0)

    # ------------------------------------------------------------------ flags
    def test_a_flag_change_is_persisted_and_audited(self):
        record = self.service.stage(FEATURES, now=self.now,
                                    flags={"dark_mode": {"enabled": True, "rollout": 10}})
        self.service.set_flag("dark_mode", enabled=False, now=self.now + 1)
        stored = json.loads(self.store.meta_get("release:" + record["release_id"]))
        self.assertFalse(stored["flags"]["dark_mode"]["enabled"])
        self.assertEqual(stored["history"][-1]["event"], "flag_changed")

    def test_the_view_is_json_safe_and_names_both_endpoints(self):
        self.service.stage(FEATURES, now=self.now)
        view = self.service.view(now=self.now + 1)
        json.dumps(view)
        self.assertEqual(view["release"]["state"], release.STATE_STAGED)
        self.assertIn("staging", view["endpoints"])
        self.assertIn("production", view["endpoints"])
        self.assertIn("samples", view["samples"])

    def test_an_empty_service_reports_no_release(self):
        view = self.service.view()
        self.assertIsNone(view["release"])
        self.assertEqual(view["samples"]["samples"], 0)


if __name__ == "__main__":
    unittest.main()
