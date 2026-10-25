"""Protect the bundled examples' synthetic guards and evidence relationships.

Spec: knowledge/operations/telemetry-contract.md
"""

from contextlib import redirect_stderr
import copy
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
try:
    import validate_fixtures as fixtures
finally:
    sys.path.pop(0)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.data, self.events = fixtures.read_fixtures()

    def test_bundled_fixtures_preserve_deduplicated_accounting(self):
        self.assertEqual(fixtures.validate(self.data, self.events), {
            "json_files": 5, "deliveries": 13, "unique_events": 12,
            "charges": 2, "inference_cost_usd": "0.05"})

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for text in ('{"x":1,"x":2}', '{"nested":{"x":1,"x":1}}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}',
                     '{"x":1e999}', '{"x":-1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                fixtures.strict_json(text)
        self.assertEqual(fixtures.strict_json('{"fraction":1.25,"unknown":null}'),
                         {"fraction": 1.25, "unknown": None})

    def test_all_fixture_labels_must_be_synthetic(self):
        for name in fixtures.JSON_FILES:
            with self.subTest(name=name):
                data = copy.deepcopy(self.data)
                data[name]["example_only"] = False
                with self.assertRaisesRegex(ValueError, "example_only"):
                    fixtures.validate(data, self.events)
        self.events[0]["example_only"] = 1
        with self.assertRaisesRegex(ValueError, "example_only"):
            fixtures.validate(self.data, self.events)

    def test_observe_and_shadow_guards_cannot_be_enabled(self):
        cases = (("run-manifest.json", "mode", "canary"),
                 ("run-manifest.json", "environment", "production"),
                 ("routing-policy.json", "mode", "canary"),
                 ("routing-policy.json", "application_enabled", True),
                 ("routing-policy.json", "application_enabled", 0),
                 ("routing-policy.json", "adaptive_learning_enabled", True))
        for name, field, value in cases:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data[name][field] = value
                with self.assertRaisesRegex(ValueError, "observe/shadow"):
                    fixtures.validate(data, self.events)
        self.data["routing-policy.json"]["profiles"][0]["live_eligible"] = True
        with self.assertRaisesRegex(ValueError, "observe/shadow"):
            fixtures.validate(self.data, self.events)

    def test_policy_and_profile_bindings_must_match(self):
        for field in ("controller_policy_id", "active_profile_id"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["run-manifest.json"][field] = "unknown"
                with self.assertRaisesRegex(ValueError, "policy/profile"):
                    fixtures.validate(data, self.events)
        self.data["routing-policy.json"]["baseline_profile_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "policy/profile"):
            fixtures.validate(self.data, self.events)

    def test_duplicate_profile_identity_is_rejected(self):
        profiles = self.data["routing-policy.json"]["profiles"]
        profiles.append(copy.deepcopy(profiles[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate profile"):
            fixtures.validate(self.data, self.events)

    def test_events_cannot_override_observe_and_shadow_controls(self):
        cases = (("run.started", "environment", "production"),
                 ("run.started", "active_profile_id", "example-low-cost"),
                 ("routing.decided", "mode", "canary"),
                 ("routing.decided", "applied", True),
                 ("routing.decided", "applied", 0),
                 ("routing.decided", "actual_profile_id", "example-low-cost"),
                 ("inference.started", "profile_id", "example-low-cost"))
        for event_type, field, value in cases:
            with self.subTest(event_type=event_type, field=field, value=value):
                events = copy.deepcopy(self.events)
                event = next(event for event in events if event["event_type"] == event_type)
                event["data"][field] = value
                with self.assertRaises(ValueError):
                    fixtures.validate(self.data, events)

    def test_routing_application_event_is_rejected(self):
        event = next(event for event in self.events if event["event_type"] == "routing.decided")
        event["event_type"] = "routing.applied"
        with self.assertRaisesRegex(ValueError, "Routing application is disabled"):
            fixtures.validate(self.data, self.events)

    def test_outcome_task_run_and_artifact_must_match(self):
        for field, value in (("task_id", "other-task"), ("run_ids", ["other-run"]),
                             ("artifact_digest", "other-artifact"), ("acceptance_stage", "other-stage")):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["task-outcome.json"][field] = value
                with self.assertRaisesRegex(ValueError, "task/run/artifact"):
                    fixtures.validate(data, self.events)

    def test_outcome_checks_must_match_the_manifest(self):
        for check_ids in (["acceptance-test"], ["unknown"],
                          ["acceptance-test", "scope-review", "scope-review"]):
            with self.subTest(check_ids=check_ids):
                data = copy.deepcopy(self.data)
                data["task-outcome.json"]["check_ids"] = check_ids
                with self.assertRaisesRegex(ValueError, "check references"):
                    fixtures.validate(data, self.events)

    def test_event_task_run_artifact_and_profile_references_must_match(self):
        for field in ("task_id", "run_id"):
            with self.subTest(field=field):
                events = copy.deepcopy(self.events)
                events[0][field] = "unknown"
                with self.assertRaisesRegex(ValueError, "Event task/run"):
                    fixtures.validate(self.data, events)
        for field, event_type in (("artifact_digest", "artifact.exported"),
                                  ("suggested_profile_id", "routing.decided")):
            with self.subTest(field=field):
                events = copy.deepcopy(self.events)
                event = next(event for event in events if event["event_type"] == event_type)
                event["data"][field] = "unknown"
                with self.assertRaises(ValueError):
                    fixtures.validate(self.data, events)

    def test_identical_redelivery_does_not_add_a_charge(self):
        self.events.append(copy.deepcopy(self.events[6]))
        result = fixtures.validate(self.data, self.events)
        self.assertEqual(result["deliveries"], 14)
        self.assertEqual((result["unique_events"], result["charges"], result["inference_cost_usd"]),
                         (12, 2, "0.05"))

    def test_artifact_links_cannot_be_omitted(self):
        for event_type in ("artifact.exported", "validation.completed", "run.ended", "task.outcome_recorded"):
            with self.subTest(event_type=event_type):
                events = copy.deepcopy(self.events)
                event = next(event for event in events if event["event_type"] == event_type)
                del event["data"]["artifact_digest"]
                with self.assertRaisesRegex(ValueError, "artifact binding"):
                    fixtures.validate(self.data, events)

    def test_conflicting_redelivery_is_rejected(self):
        conflicting = copy.deepcopy(self.events[6])
        conflicting["data"]["amount"] = "0.09"
        self.events.append(conflicting)
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            fixtures.validate(self.data, self.events)

    def test_boolean_is_not_an_identical_numeric_redelivery(self):
        conflicting = copy.deepcopy(next(event for event in self.events
                                         if event["event_type"] == "routing.decided"))
        conflicting["data"]["assignment_probability"] = True
        self.events.append(conflicting)
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            fixtures.validate(self.data, self.events)

    def test_validation_evidence_cannot_be_missing_or_failed(self):
        events = [event for event in self.events if event["event_type"] != "validation.completed"]
        with self.assertRaisesRegex(ValueError, "validation check references"):
            fixtures.validate(self.data, events)
        validation = next(event for event in self.events if event["event_type"] == "validation.completed")
        validation["data"]["result"] = "fail"
        with self.assertRaisesRegex(ValueError, "does not support"):
            fixtures.validate(self.data, self.events)

    def test_missing_reconciled_attempt_cannot_disappear_from_cost(self):
        self.events = [event for event in self.events if event["event_type"] != "usage.reconciled"]
        self.data["task-outcome.json"]["cost"].update(known_amount="0.03", included_charge_ids=["charge-02"])
        with self.assertRaisesRegex(ValueError, "every inference attempt"):
            fixtures.validate(self.data, self.events)

    def test_distinct_observations_cannot_reuse_one_charge(self):
        extra = copy.deepcopy(self.events[6])
        extra["event_id"] = "another-event"
        self.events.append(extra)
        with self.assertRaisesRegex(ValueError, "one observation per charge"):
            fixtures.validate(self.data, self.events)

    def test_charge_references_amounts_and_scope_are_checked(self):
        cases = (("included_charge_ids", ["charge-02"]), ("known_amount", "0.08"),
                 ("currency", "EUR"), ("unresolved_charge_count", 1),
                 ("scope", "all_in"), ("all_in_task_cost_complete", True))
        for field, value in cases:
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["task-outcome.json"]["cost"][field] = value
                with self.assertRaises(ValueError):
                    fixtures.validate(data, self.events)
        for value in ("NaN", "Infinity", "-0.01", "not-money", 0.03):
            with self.subTest(amount=value):
                events = copy.deepcopy(self.events)
                for event in events:
                    if event["event_type"] == "usage.observed":
                        event["data"]["amount"] = value
                with self.assertRaises(ValueError):
                    fixtures.validate(self.data, events)

    def test_ci_gate_reuses_the_paired_cohort_checks(self):
        self.data["cohort-comparison.json"]["policies"][1]["tasks"].pop()
        with self.assertRaisesRegex(ValueError, "same task identities"):
            fixtures.validate(self.data, self.events)

    def test_invalid_input_reports_failure_without_a_traceback(self):
        error = io.StringIO()
        with patch.object(fixtures, "read_fixtures", side_effect=ValueError("Duplicate JSON object key")):
            with redirect_stderr(error):
                self.assertEqual(fixtures.main(), 1)
        self.assertIn("Invalid synthetic fixtures", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_cli_preserves_fixture_files(self):
        paths = [ROOT / "examples" / name for name in (*fixtures.JSON_FILES, "session-events.jsonl")]
        before = [path.read_bytes() for path in paths]
        result = subprocess.run([sys.executable, str(ROOT / "examples/validate_fixtures.py")],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"inference_cost_usd": "0.05"', result.stdout)
        self.assertEqual([path.read_bytes() for path in paths], before)


if __name__ == "__main__":
    unittest.main()
