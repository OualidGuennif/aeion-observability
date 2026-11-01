"""Deterministic releases: identity, monotone cohorts, flags, plan and transitions."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import release

FEATURES = [
    {"id": "001", "title": "App skeleton", "digest": "a" * 64},
    {"id": "002", "title": "Settings", "digest": "b" * 64},
]
PLAN = ({"percent": 25, "dwell_seconds": 10, "label": "canary"},
        {"percent": 50, "dwell_seconds": 20, "label": "half"},
        {"percent": 100, "dwell_seconds": 0, "label": "full"})


def staged(now=1_000_000_000):
    return release.create(FEATURES, now_ns=now, plan=PLAN,
                          flags={"dark_mode": {"enabled": True, "rollout": 50}})


class IdentityTests(unittest.TestCase):
    def test_release_id_is_content_addressed(self):
        first = release.release_id(FEATURES)
        self.assertEqual(first, release.release_id(list(reversed(FEATURES))))
        changed = [dict(FEATURES[0]), dict(FEATURES[1], digest="c" * 64)]
        self.assertNotEqual(first, release.release_id(changed))

    def test_an_empty_release_is_refused(self):
        with self.assertRaisesRegex(release.ReleaseError, "release_needs_a_feature"):
            release.release_id([])
        with self.assertRaisesRegex(release.ReleaseError, "feature_missing:digest"):
            release.create([{"id": "001", "title": "x"}])


class CohortTests(unittest.TestCase):
    def test_a_client_always_lands_in_the_same_bucket(self):
        seed = release.release_id(FEATURES)
        self.assertEqual(release.bucket(seed, "agent-42"), release.bucket(seed, "agent-42"))
        self.assertNotEqual(release.bucket(seed, "agent-42"), release.bucket(seed, "agent-43"))

    def test_cohorts_are_monotone_as_the_rollout_widens(self):
        seed = release.release_id(FEATURES)
        clients = [f"agent-{index}" for index in range(2000)]
        cohort25 = {c for c in clients if release.in_cohort(seed, c, 25)}
        cohort50 = {c for c in clients if release.in_cohort(seed, c, 50)}
        cohort100 = {c for c in clients if release.in_cohort(seed, c, 100)}
        self.assertTrue(cohort25 <= cohort50 <= cohort100)
        self.assertEqual(len(cohort100), len(clients))
        self.assertAlmostEqual(len(cohort25) / len(clients), 0.25, delta=0.03)
        self.assertAlmostEqual(len(cohort50) / len(clients), 0.50, delta=0.03)

    def test_zero_and_hundred_are_exact(self):
        seed = release.release_id(FEATURES)
        self.assertFalse(release.in_cohort(seed, "agent-1", 0))
        self.assertTrue(release.in_cohort(seed, "agent-1", 100))
        with self.assertRaisesRegex(release.ReleaseError, "client_key_required"):
            release.in_cohort(seed, "", 50)


class FlagTests(unittest.TestCase):
    def test_an_unknown_or_disabled_flag_is_never_on(self):
        seed = release.release_id(FEATURES)
        self.assertFalse(release.flag_state({}, "nope", seed, "agent-1")["enabled"])
        flags = {"x": {"enabled": False, "rollout": 100}}
        self.assertFalse(release.flag_state(flags, "x", seed, "agent-1")["enabled"])

    def test_a_flag_follows_its_rollout_and_is_monotone(self):
        seed = release.release_id(FEATURES)
        flags = {"dark_mode": {"enabled": True, "rollout": 40}}
        clients = [f"agent-{index}" for index in range(1000)]
        on40 = {c for c in clients if release.flag_state(flags, "dark_mode", seed, c)["enabled"]}
        flags["dark_mode"]["rollout"] = 80
        on80 = {c for c in clients if release.flag_state(flags, "dark_mode", seed, c)["enabled"]}
        self.assertTrue(on40 <= on80)
        self.assertAlmostEqual(len(on40) / len(clients), 0.40, delta=0.05)

    def test_changing_a_flag_is_recorded(self):
        current = staged()
        release.set_flag(current, "dark_mode", enabled=False, now_ns=1_000_000_001)
        self.assertFalse(current["flags"]["dark_mode"]["enabled"])
        self.assertEqual(current["history"][-1]["event"], "flag_changed")


class TransitionTests(unittest.TestCase):
    def test_promote_starts_the_first_step_at_25_percent(self):
        current = staged()
        release.promote(current, now_ns=1_000_000_001)
        self.assertEqual(current["state"], release.STATE_CANARY)
        self.assertEqual(current["percent"], 25)
        self.assertEqual(current["step_started_ns"], 1_000_000_001)

    def test_a_staged_release_serves_nobody_until_validated(self):
        current = staged()
        self.assertEqual(current["percent"], 0)
        self.assertEqual(current["state"], release.STATE_STAGED)
        self.assertFalse(release.step_status(current, 2_000_000_000)["due"])

    def test_advance_waits_for_the_dwell_then_widens(self):
        current = staged()
        release.promote(current, now_ns=1_000_000_000)
        with self.assertRaisesRegex(release.ReleaseError, "dwell_not_finished:10"):
            release.advance(current, now_ns=1_000_000_000)
        status = release.step_status(current, now_ns=11_000_000_000)
        self.assertTrue(status["due"])
        release.advance(current, now_ns=11_000_000_000)
        self.assertEqual(current["percent"], 50)
        release.advance(current, now_ns=32_000_000_000)
        self.assertEqual(current["state"], release.STATE_RELEASED)
        self.assertEqual(current["percent"], 100)

    def test_a_failing_gate_blocks_the_advance(self):
        current = staged()
        release.promote(current, now_ns=1_000_000_000)
        with self.assertRaisesRegex(release.ReleaseError, "gate_blocks_advance:rollback"):
            release.advance(current, now_ns=99_000_000_000, verdict="rollback")

    def test_immediate_full_deploy_skips_the_dwells(self):
        current = staged()
        release.deploy_now(current, now_ns=1_000_000_002)
        self.assertEqual(current["state"], release.STATE_RELEASED)
        self.assertEqual(current["percent"], 100)
        self.assertEqual(current["history"][-1]["event"], "immediate_full_deploy")

    def test_rollback_serves_nobody_and_records_why(self):
        current = staged()
        release.promote(current, now_ns=1_000_000_000)
        release.rollback(current, now_ns=1_000_000_003, reason="five_xx")
        self.assertEqual(current["percent"], 0)
        self.assertEqual(current["state"], release.STATE_ROLLED_BACK)
        self.assertEqual(current["rollback_reason"], "five_xx")

    def test_illegal_transitions_are_refused(self):
        current = staged()
        with self.assertRaisesRegex(release.ReleaseError, "cannot_advance_from"):
            release.advance(current)
        release.promote(current)
        with self.assertRaisesRegex(release.ReleaseError, "cannot_promote_from"):
            release.promote(current)

    def test_status_is_json_safe_and_carries_the_evidence(self):
        current = staged()
        release.promote(current, now_ns=1_000_000_000)
        view = release.status(current, now_ns=4_000_000_000,
                              gate={"verdict": "continue", "samples": 2})
        self.assertEqual(view["percent"], 25)
        self.assertEqual(view["gate"]["verdict"], "continue")
        self.assertEqual(view["step_status"]["elapsed_seconds"], 3)
        self.assertEqual(len(view["features"]), 2)

    def test_a_compressed_drill_is_recorded_as_scaled(self):
        current = release.create(FEATURES, now_ns=1, scale=0.001)
        self.assertEqual(current["scale"], 0.001)
        self.assertEqual(current["plan"][0]["dwell_seconds"], int(6 * 3600 * 0.001))


if __name__ == "__main__":
    unittest.main()
