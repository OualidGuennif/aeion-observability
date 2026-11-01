"""The canary monitor: rules over recorded samples, not another model.

Every 5 minutes the playground records one sample of what the load balancer actually saw — request
count, 5xx, error rate, p95 latency, cache hit rate — and this module decides whether the rollout
may continue. The same samples always produce the same verdict, the policy is pinned data, and a
missing or unreadable sample is a *hold*, never a silent pass.

Thresholds are deliberately conservative: one 5xx is enough to stop a rollout, because a canary
that only fails 0.5% of the time still fails thousands of agents at scale.
"""
import json

POLICY = {
    "min_samples": 4,
    "max_error_rate": 0.01,
    "max_p95_ms": 400,
    "min_cache_hit_rate": 0.50,
    "max_5xx": 0,
    "max_requests_per_sample": 200_000,
}

VERDICTS = ("continue", "insufficient", "hold", "rollback")


class CanaryError(ValueError):
    """A sample that cannot be trusted is refused, never interpreted."""


def validate_sample(sample):
    """A sample must carry the numbers the policy reads, as numbers, in range."""
    required = ("requests", "errors_5xx", "error_rate", "p95_ms", "cache_hit_rate")
    missing = [key for key in required if key not in sample]
    if missing:
        raise CanaryError("sample_missing:" + ",".join(missing))
    for key in ("requests", "errors_5xx"):
        if not isinstance(sample[key], int) or sample[key] < 0:
            raise CanaryError(f"sample_invalid:{key}")
    for key in ("error_rate", "cache_hit_rate"):
        value = sample[key]
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise CanaryError(f"sample_invalid:{key}")
    if not isinstance(sample["p95_ms"], (int, float)) or sample["p95_ms"] < 0:
        raise CanaryError("sample_invalid:p95_ms")
    return True


def evaluate(samples, policy=None, required_samples=None):
    """`continue` | `hold` | `rollback`, with the first violation as evidence."""
    policy = dict(POLICY if policy is None else policy)
    needed = policy["min_samples"] if required_samples is None else int(required_samples)
    for sample in samples:
        validate_sample(sample)
    active = [sample for sample in samples if sample["requests"] > 0]
    if not active:
        return {"verdict": "insufficient", "reason": "no_traffic", "violations": [],
                "samples": len(samples)}
    violations = []
    for index, sample in enumerate(active):
        if sample["errors_5xx"] > policy["max_5xx"]:
            violations.append({"at": index, "code": "five_xx", "value": sample["errors_5xx"],
                               "limit": policy["max_5xx"]})
        if sample["error_rate"] > policy["max_error_rate"]:
            violations.append({"at": index, "code": "error_rate", "value": sample["error_rate"],
                               "limit": policy["max_error_rate"]})
        if sample["p95_ms"] > policy["max_p95_ms"]:
            violations.append({"at": index, "code": "p95_ms", "value": sample["p95_ms"],
                               "limit": policy["max_p95_ms"]})
        if sample["cache_hit_rate"] < policy["min_cache_hit_rate"]:
            violations.append({"at": index, "code": "cache_hit_rate", "value": sample["cache_hit_rate"],
                               "limit": policy["min_cache_hit_rate"]})
        if sample["requests"] > policy["max_requests_per_sample"]:
            violations.append({"at": index, "code": "request_burst", "value": sample["requests"],
                               "limit": policy["max_requests_per_sample"]})
    result = {"samples": len(active), "violations": violations[:10],
              "policy": policy, "first_violation": violations[0] if violations else None}
    if violations:
        # A single 5xx or an error-rate breach is a rollback; latency and cache are recoverable.
        hard = {violation["code"] for violation in violations} & {"five_xx", "error_rate"}
        result["verdict"] = "rollback" if hard else "hold"
        result["reason"] = "policy_violation:" + sorted({v["code"] for v in violations})[0]
        return result
    if len(active) < needed:
        # Not a failure: there is simply not enough evidence to widen the rollout yet.
        result["verdict"] = "insufficient"
        result["reason"] = f"insufficient_samples:{len(active)}/{needed}"
        return result
    result["verdict"] = "continue"
    result["reason"] = "within_policy"
    return result


def sample_from_stats(stats):
    """Turn one `/__lb/stats` reading into a sample; unknown numbers make the sample invalid."""
    if not isinstance(stats, dict):
        raise CanaryError("stats_not_an_object")
    requests = int(stats.get("requests", 0))
    errors = int(stats.get("status_5xx", 0))
    hits = int(stats.get("cache_hits", 0))
    misses = int(stats.get("cache_misses", 0))
    cache_total = hits + misses
    return {
        "requests": requests,
        "errors_5xx": errors,
        "error_rate": (errors / requests) if requests else 0.0,
        "p95_ms": float(stats.get("p95_ms", 0.0)),
        "cache_hit_rate": (hits / cache_total) if cache_total else 0.0,
    }


def record(samples, sample, limit=48):
    """Append one sample to a bounded series; the oldest is dropped, order is preserved."""
    validate_sample(sample)
    series = list(samples or []) + [sample]
    return series[-limit:]


def summarise(samples, policy=None):
    """The compact series the front draws: time, error rate, p95, cache hit."""
    policy = POLICY if policy is None else policy
    points, worst = [], 0.0
    for sample in samples or []:
        validate_sample(sample)
        worst = max(worst, float(sample["error_rate"]))
        points.append({"requests": sample["requests"], "error_rate": sample["error_rate"],
                       "p95_ms": sample["p95_ms"], "cache_hit_rate": sample["cache_hit_rate"]})
    return {"points": points[-48:], "worst_error_rate": worst, "policy": policy,
            "samples": len(points)}


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
