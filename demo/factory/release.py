"""Deterministic releases: content-addressed, audience-bucketed, flag-versioned.

A release is a set of built features pinned by digest. Its identity is the digest of that set, so
two identical sets are one release and any change is a new one. Everything a release can do is a
pure function of `(release, now, samples)`:

* audience bucketing is `sha256(release|client) % 100`, which is stable per client and **monotone**:
  the 25% cohort is a subset of the 50% cohort, so a user never falls back to the old version as
  the rollout widens;
* the promotion plan is data, not code: 25% for 6 h, 50% for 12 h, then 100%;
* a flag is `enabled` plus a `rollout` percentage evaluated with the same bucketing, so a flag can
  be switched off without a deploy and cannot be on for a user who is not in its cohort.

The plan's dwells are real. `scale` exists only for the local playground and is recorded in the
release, so a compressed drill can never be mistaken for a real one.
"""
import hashlib
import json
import time

STATE_STAGED = "staged"
STATE_CANARY = "canary"
STATE_RELEASED = "released"
STATE_ROLLED_BACK = "rolled_back"
STATE_HELD = "held"

PLAN = (
    {"percent": 25, "dwell_seconds": 6 * 3600, "label": "canary"},
    {"percent": 50, "dwell_seconds": 12 * 3600, "label": "half"},
    {"percent": 100, "dwell_seconds": 0, "label": "full"},
)


class ReleaseError(ValueError):
    """An impossible transition, refused rather than guessed."""


def digest(*parts):
    return hashlib.sha256("\x1f".join(str(part) for part in parts).encode()).hexdigest()


def release_id(features):
    """The identity of a release: the sorted (feature id, artifact digest) pairs it ships."""
    pairs = sorted((str(f["id"]), str(f["digest"])) for f in features)
    if not pairs:
        raise ReleaseError("release_needs_a_feature")
    return digest(*(f"{fid}:{art}" for fid, art in pairs))[:32]


def bucket(seed, client):
    """A stable 0..99 bucket for a client under a seed; the same input always gives the same one."""
    if not isinstance(client, str) or not client:
        raise ReleaseError("client_key_required")
    value = int(hashlib.sha256(f"{seed}|{client}".encode()).hexdigest()[:8], 16)
    return value % 100


def in_cohort(seed, client, percent):
    percent = int(percent)
    if percent <= 0:
        return False
    if percent >= 100:
        return True
    return bucket(seed, client) < percent


def flag_state(flags, name, seed, client):
    """`{enabled, rollout}` evaluated for one client; unknown flags are off, never on."""
    flag = (flags or {}).get(name)
    if not isinstance(flag, dict):
        return {"enabled": False, "rollout": 0, "reason": "unknown_flag"}
    if not flag.get("enabled", False):
        return {"enabled": False, "rollout": 0, "reason": "disabled"}
    rollout = int(flag.get("rollout", 0))
    on = in_cohort(f"{seed}|flag:{name}", client, rollout)
    return {"enabled": on, "rollout": rollout, "reason": "in_cohort" if on else "out_of_cohort"}


def create(features, now_ns=None, flags=None, plan=PLAN, scale=1.0):
    """Build a staged release from built features; nothing is live until `promote` is called."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    normalised = []
    for feature in features:
        missing = [key for key in ("id", "title", "digest") if not feature.get(key)]
        if missing:
            raise ReleaseError("feature_missing:" + ",".join(missing))
        normalised.append({"id": str(feature["id"]), "title": str(feature["title"]),
                           "digest": str(feature["digest"])})
    steps = [{"percent": int(step["percent"]),
              "dwell_seconds": int(step["dwell_seconds"] * scale),
              "label": step.get("label", "")} for step in plan]
    if [step["percent"] for step in steps] != sorted(step["percent"] for step in steps):
        raise ReleaseError("plan_not_monotone")
    return {
        "release_id": release_id(normalised),
        "features": normalised,
        "created_ns": now_ns,
        "state": STATE_STAGED,
        "step": -1,
        "percent": 0,
        "step_started_ns": None,
        "validated_ns": None,
        "released_ns": None,
        "rolled_back_ns": None,
        "rollback_reason": None,
        "plan": steps,
        "scale": float(scale),
        "flags": dict(flags or {}),
        "history": [{"at_ns": now_ns, "event": "staged", "detail": "built, not promoted"}],
    }


def _record(release, now_ns, event, detail=None):
    release["history"].append({"at_ns": now_ns, "event": event, "detail": detail})
    return release


def promote(release, now_ns=None):
    """Validate a staged release: it starts reaching real traffic at the first plan step."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    if release["state"] != STATE_STAGED:
        raise ReleaseError(f"cannot_promote_from:{release['state']}")
    release["state"] = STATE_CANARY
    release["step"] = 0
    release["percent"] = release["plan"][0]["percent"]
    release["step_started_ns"] = now_ns
    release["validated_ns"] = now_ns
    return _record(release, now_ns, "validated", f"canary {release['percent']}%")


def deploy_now(release, now_ns=None):
    """The operator's "immediate full deploy": skip the dwells, keep the release identity."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    if release["state"] not in {STATE_STAGED, STATE_CANARY, STATE_HELD}:
        raise ReleaseError(f"cannot_deploy_now_from:{release['state']}")
    release["state"] = STATE_RELEASED
    release["step"] = len(release["plan"]) - 1
    release["percent"] = 100
    release["validated_ns"] = release.get("validated_ns") or now_ns
    release["released_ns"] = now_ns
    release["step_started_ns"] = now_ns
    return _record(release, now_ns, "immediate_full_deploy", "operator skipped the dwells")


def step_status(release, now_ns=None):
    """Elapsed and remaining dwell of the current step; never negative, never guessed."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    if release["state"] != STATE_CANARY or release["step"] < 0:
        return {"elapsed_seconds": 0, "dwell_seconds": 0, "remaining_seconds": 0, "due": False}
    step = release["plan"][release["step"]]
    started = release["step_started_ns"]
    elapsed = max(0, (now_ns - started) // 1_000_000_000) if started else 0
    dwell = step["dwell_seconds"]
    return {"elapsed_seconds": elapsed, "dwell_seconds": dwell,
            "remaining_seconds": max(0, dwell - elapsed), "due": elapsed >= dwell}


def advance(release, now_ns=None, verdict="continue"):
    """Move to the next plan step only when the dwell is over and the monitor says continue."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    if release["state"] != STATE_CANARY:
        raise ReleaseError(f"cannot_advance_from:{release['state']}")
    if verdict != "continue":
        raise ReleaseError(f"gate_blocks_advance:{verdict}")
    status = step_status(release, now_ns)
    if not status["due"]:
        raise ReleaseError(f"dwell_not_finished:{status['remaining_seconds']}")
    if release["step"] + 1 >= len(release["plan"]):
        release["state"] = STATE_RELEASED
        release["released_ns"] = now_ns
        return _record(release, now_ns, "released", "100%")
    release["step"] += 1
    step = release["plan"][release["step"]]
    release["percent"] = step["percent"]
    release["step_started_ns"] = now_ns
    if step["percent"] >= 100:
        release["state"] = STATE_RELEASED
        release["released_ns"] = now_ns
        return _record(release, now_ns, "released", "100%")
    return _record(release, now_ns, "advanced", f"{step['percent']}%")


def hold(release, now_ns=None, reason="gate_hold"):
    now_ns = time.time_ns() if now_ns is None else now_ns
    release["state"] = STATE_HELD
    return _record(release, now_ns, "held", reason)


def rollback(release, now_ns=None, reason="operator"):
    now_ns = time.time_ns() if now_ns is None else now_ns
    release["state"] = STATE_ROLLED_BACK
    release["percent"] = 0
    release["rolled_back_ns"] = now_ns
    release["rollback_reason"] = reason
    return _record(release, now_ns, "rolled_back", reason)


def set_flag(release, name, enabled=None, rollout=None, now_ns=None):
    """Flags move with the release: a change is recorded, and a missing flag is never enabled."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    if not isinstance(name, str) or not name:
        raise ReleaseError("flag_name_required")
    flag = dict(release["flags"].get(name) or {"enabled": False, "rollout": 0})
    if enabled is not None:
        flag["enabled"] = bool(enabled)
    if rollout is not None:
        flag["rollout"] = max(0, min(100, int(rollout)))
    release["flags"][name] = flag
    return _record(release, now_ns, "flag_changed", f"{name}={json.dumps(flag, sort_keys=True)}")


def status(release, now_ns=None, gate=None):
    """One JSON-safe view of the release for the front: state, step, dwell, gate, flags."""
    now_ns = time.time_ns() if now_ns is None else now_ns
    return {
        "release_id": release["release_id"],
        "state": release["state"],
        "percent": release["percent"],
        "step": release["step"],
        "steps": release["plan"],
        "step_status": step_status(release, now_ns),
        "validated_ns": release["validated_ns"],
        "released_ns": release["released_ns"],
        "rollback_reason": release["rollback_reason"],
        "scale": release["scale"],
        "features": release["features"],
        "flags": release["flags"],
        "gate": gate,
        "history": release["history"][-20:],
    }
