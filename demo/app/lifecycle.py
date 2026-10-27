"""Campaign order and restart recovery; pure functions with no provider, sandbox or network access."""
from profiles import PROFILES, available
from scenarios import SCENARIOS


def plan(repeats=2):
    # One source for the executed order and the advertised total; expired profiles are skipped.
    steps = []
    for repeat in range(repeats):
        for i, task_id in enumerate(SCENARIOS):
            keys = list(PROFILES)
            shift = (i + repeat) % len(keys)
            steps.extend((repeat, task_id, profile) for profile in keys[shift:] + keys[:shift] if available(profile))
    return steps


def recover(record):
    """Close state left by a stopped controller; never retries provider work. Returns True if changed."""
    changed = False
    if record.get("status") == "running":
        record["status"] = "interrupted"
        changed = True
    if record.get("postprocessing"):
        record["postprocessing"] = False
        changed = True
    if record.get("memory", {}).get("status") == "pending":
        record["memory"] = {"status": "interrupted"}
        changed = True
    return changed
