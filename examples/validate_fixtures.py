#!/usr/bin/env python3
"""Check the bundled synthetic examples without qualifying a runtime or calling a provider.

Spec: knowledge/operations/telemetry-contract.md
"""

from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import sys

from compare_cohorts import summarize


JSON_FILES = ("cohort-comparison.json", "provider-requests.json", "routing-policy.json",
              "run-manifest.json", "task-outcome.json")


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON object key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Non-finite JSON number: " + value)


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("JSON number overflows to a non-finite value")
    return number


def strict_json(text):
    return json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant,
                      parse_float=finite_float)


def read_fixtures():
    root = Path(__file__).resolve().parent
    fixtures = {name: strict_json((root / name).read_text(encoding="utf-8")) for name in JSON_FILES}
    events = [strict_json(line) for line in (root / "session-events.jsonl").read_text(encoding="utf-8").splitlines()
              if line.strip()]
    return fixtures, events


def money(value):
    if not isinstance(value, str):
        raise ValueError("Fixture amounts must be decimal strings")
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Invalid fixture amount") from error
    if not amount.is_finite() or amount < 0:
        raise ValueError("Fixture amounts must be finite and nonnegative")
    return amount


def validate(fixtures, events):
    # Keep every input explicitly fictional, including each delivered event.
    if any(not isinstance(record, dict) or record.get("example_only") is not True
           for record in [*fixtures.values(), *events]):
        raise ValueError("Every fixture and event must be marked example_only=true")
    if not summarize(fixtures["cohort-comparison.json"]):
        raise ValueError("The cohort example must contain a policy")
    manifest = fixtures["run-manifest.json"]
    policy = fixtures["routing-policy.json"]
    outcome = fixtures["task-outcome.json"]
    if (manifest["mode"] != "observe" or manifest["environment"] != "evaluation"
            or policy["mode"] != "shadow" or policy["application_enabled"] is not False
            or policy["adaptive_learning_enabled"] is not False
            or any(profile["live_eligible"] is not False for profile in policy["profiles"])):
        raise ValueError("Fixtures must remain observe/shadow only and not live eligible")

    # Bind the recorded session to the policy, task and artifact it actually describes.
    profile_ids = {profile["id"] for profile in policy["profiles"]}
    if len(profile_ids) != len(policy["profiles"]):
        raise ValueError("Duplicate profile identity")
    if (manifest["controller_policy_id"] != policy["policy_id"]
            or manifest["active_profile_id"] not in profile_ids
            or policy["baseline_profile_id"] != manifest["active_profile_id"]):
        raise ValueError("Manifest policy/profile binding mismatch")
    if (outcome["task_id"] != manifest["task_id"] or outcome["run_ids"] != [manifest["run_id"]]
            or outcome["artifact_digest"] != manifest["artifact_digest"]
            or outcome["acceptance_stage"] != manifest["acceptance_stage"]):
        raise ValueError("Outcome task/run/artifact binding mismatch")
    expected_checks = set(manifest["acceptance"]["check_ids"])
    if (not expected_checks or len(expected_checks) != len(manifest["acceptance"]["check_ids"])
            or set(outcome["check_ids"]) != expected_checks
            or len(outcome["check_ids"]) != len(expected_checks)):
        raise ValueError("Outcome check references mismatch")

    # Redelivery may repeat the same record, but must not replace its contents.
    unique = {}
    for event in events:
        if (event["task_id"], event["run_id"]) != (manifest["task_id"], manifest["run_id"]):
            raise ValueError("Event task/run binding mismatch")
        key = (event["producer"]["id"], event["producer"]["boot_id"], event["event_id"])
        if key in unique and (json.dumps(unique[key], sort_keys=True, allow_nan=False)
                              != json.dumps(event, sort_keys=True, allow_nan=False)):
            raise ValueError("Conflicting duplicate event")
        unique[key] = event
        data = event["data"]
        if (("artifact_digest" in data or event["event_type"] in {
                "artifact.exported", "validation.completed", "run.ended", "task.outcome_recorded"})
                and data.get("artifact_digest") != outcome["artifact_digest"]):
            raise ValueError("Event artifact binding mismatch")
        for field in ("profile_id", "active_profile_id", "actual_profile_id",
                      "suggested_profile_id", "selected_profile_id"):
            if data.get(field) is not None and data[field] not in profile_ids:
                raise ValueError("Unknown event profile reference")

    # Corroborate the fictional check references before accepting the recorded outcome.
    completed_checks = set()
    for event in unique.values():
        if event["event_type"] == "validation.completed":
            data = event["data"]
            if data["result"] != "pass" or data["artifact_digest"] != outcome["artifact_digest"]:
                raise ValueError("Validation does not support the outcome")
            completed_checks.update(data["check_ids"])
    if completed_checks != expected_checks:
        raise ValueError("Missing or unexpected validation check references")

    # This example has one complete charge per attempt after reconciliation.
    attempts = {event["data"]["attempt_id"] for event in unique.values()
                if event["event_type"] == "inference.started"}
    charges = {}
    for event in unique.values():
        if event["event_type"] not in {"usage.observed", "usage.reconciled"}:
            continue
        charge = event["data"]
        if charge["charge_id"] in charges:
            raise ValueError("The fixture requires one observation per charge")
        if charge["currency"] != "USD" or charge["completeness"] != "complete":
            raise ValueError("The fixture requires complete USD charges")
        charges[charge["charge_id"]] = charge
    if (not attempts or {charge["attempt_id"] for charge in charges.values()} != attempts
            or len(charges) != len(attempts)):
        raise ValueError("Charges must cover every inference attempt exactly once")
    cost = outcome["cost"]
    if (set(cost["included_charge_ids"]) != set(charges)
            or len(cost["included_charge_ids"]) != len(charges)
            or cost["currency"] != "USD" or cost["unresolved_charge_count"] != 0
            or cost["scope"] != "inference_only_not_all_in_task_cost"
            or cost["all_in_task_cost_complete"] is not False):
        raise ValueError("Outcome charge references or cost scope mismatch")
    total = sum((money(charge["amount"]) for charge in charges.values()), Decimal(0))
    if total != money(cost["known_amount"]):
        raise ValueError("Outcome amount does not match unique charges")
    return {"json_files": len(fixtures), "deliveries": len(events), "unique_events": len(unique),
            "charges": len(charges), "inference_cost_usd": str(total)}


def main():
    try:
        result = validate(*read_fixtures())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("Invalid synthetic fixtures: " + str(error), file=sys.stderr)
        return 1
    print("PASS: synthetic fixture consistency only; " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
