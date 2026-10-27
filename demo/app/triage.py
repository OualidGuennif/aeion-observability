"""Frozen synthetic triage task (tier 1). The verdict compares data; no model judges it."""
import json
from pathlib import Path

from json_input import loads

TRIAGE = json.loads((Path(__file__).resolve().parent.parent / "fixtures/triage.json").read_text())
ARTIFACT = "result.json"
EMPTY = '{"results": []}\n'
FIELDS = {"id", "severity", "component", "route", "duplicate_of"}


def contract(task_id):
    return (TRIAGE[task_id]["contract"] + " Submit the complete result with the submit_triage tool; a later call "
            "replaces the previous one. The supervisor checks the submitted result after you stop.")


def agent_input(task_id):
    # Only events and the label vocabulary reach the harness; expected answers never do.
    task = TRIAGE[task_id]
    return json.dumps({"labels": task["labels"], "events": task["events"]})


def solution(task_id):
    return json.dumps({"results": TRIAGE[task_id]["expected"]}) + "\n"


def check(path, task_id):
    # The harness tool validates before writing; the supervisor still treats the file as untrusted.
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768:
        raise ValueError("INVALID_ARTIFACT")
    expected = {item["id"]: item for item in TRIAGE[task_id]["expected"]}
    try:
        value = loads(path.read_bytes())
        if not isinstance(value, dict) or set(value) != {"results"} or not isinstance(value["results"], list):
            raise ValueError
        submitted = {}
        for item in value["results"]:
            if not isinstance(item, dict) or set(item) != FIELDS or item["id"] not in expected or item["id"] in submitted:
                raise ValueError
            submitted[item["id"]] = item
    except (ValueError, TypeError, UnicodeError):
        raise ValueError("INVALID_ARTIFACT") from None
    failed = [key for key, item in expected.items() if submitted.get(key) != item]
    return {"passed": len(expected) - len(failed), "failed": failed, "total": len(expected)}
