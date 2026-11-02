"""Two-vote review circuit: independent models, different families, never the author.

The circuit is the answer to "who reviews the reviewer": the model that wrote the code is
excluded from both votes, the two voters are excluded from each other's family, and any doubt
(no eligible model, an error, a malformed answer) fails closed to a human hold. A language model
never holds the final authority either: the deterministic rules in ``review.py`` run first and
their refusal is final, and the publisher still refuses anything without an approved verdict.
"""
import hashlib
import json
import time

from .models import Router, RoutingError, family, known
from .review import content_digest

MAX_PROMPT_CHARS = 6000
SYSTEM = (
    "You are an independent code reviewer. The diff below was produced by another AI agent. "
    "Look for backdoors, credential exfiltration, destructive behaviour, hidden network calls, "
    "scope that does not match the stated feature, and anything that would harm the repository. "
    'Answer only with JSON: {"verdict": "approve" or "reject", "reason": "<20 words max>"}.'
)


class CircuitError(ValueError):
    """A review circuit that cannot produce two independent votes."""


# Telemetry stores canonical outcomes; the vote itself keeps the model's approve/reject word.
_OUTCOME = {"approve": "approved", "reject": "rejected"}


def _review_input(feature_id, files, max_chars=MAX_PROMPT_CHARS):
    """Build the complete review envelope, or refuse rather than send a truncated one.

    A reviewer that saw only the first bytes of a file cannot approve the whole artifact, so
    the circuit holds when the complete changed bytes do not fit. Coverage is returned either
    way, and a caller can record it with the verdict.
    """
    parts = [SYSTEM, "", f"FEATURE: {feature_id}", "FILES:"]
    for path in sorted(files):
        parts.append(f"--- {path} ---\n{files[path]}")
    prompt = "\n".join(parts)
    coverage = {
        "complete": len(prompt) <= max_chars,
        "files": sorted(files),
        "chars": len(prompt),
        "limit_chars": max_chars,
    }
    return (prompt if coverage["complete"] else None), coverage


def _normalise(answer):
    if not isinstance(answer, dict):
        return None
    verdict = str(answer.get("verdict", "")).strip().lower()
    if verdict not in {"approve", "reject"}:
        return None
    reason = str(answer.get("reason", ""))[:120]
    return {"verdict": verdict, "reason": reason}


def two_vote_review(author_model, feature_id, files, router, complete, telemetry=None):
    """Return an approved/held verdict from two independent model votes."""
    if not files:
        return {"status": "held", "reason": "empty_diff", "votes": []}
    if not author_model or not known(author_model):
        # An unknown author cannot be excluded by family, so it cannot start a review either.
        return {"status": "held", "reason": "author_identity_unknown", "votes": [],
                "author_model": author_model}
    telemetry = telemetry if telemetry is not None else router.telemetry
    prompt, coverage = _review_input(feature_id, files)
    if prompt is None:
        # The complete bytes do not fit: two votes on an excerpt never approve the artifact.
        return {"status": "held", "reason": "review_input_too_large", "votes": [],
                "coverage": coverage, "content_digest": content_digest(files)}
    author_family = family(author_model)
    votes = []
    used_models, used_families = [author_model], [author_family]
    for index in (1, 2):
        try:
            model = router.select("review", exclude_models=used_models, exclude_families=used_families)
        except RoutingError:
            return {"status": "held", "reason": "no_independent_reviewer", "votes": votes}
        if family(model) in used_families:
            return {"status": "held", "reason": "same_family_reviewer", "votes": votes}
        started = time.monotonic()
        try:
            answer = _normalise(complete(model, prompt))
        except Exception:  # noqa: BLE001 - a failed vote is a hold, never an approval
            answer = None
        latency_ms = int((time.monotonic() - started) * 1000)
        if answer is None:
            telemetry.record(model, "review", "error", latency_ms=latency_ms)
            votes.append({"vote": index, "model": model, "family": family(model),
                          "verdict": "error", "reason": "malformed_or_failed"})
            return {"status": "held", "reason": "reviewer_failed", "votes": votes}
        telemetry.record(model, "review", _OUTCOME[answer["verdict"]], latency_ms=latency_ms)
        votes.append({"vote": index, "model": model, "family": family(model),
                      "verdict": answer["verdict"], "reason": answer["reason"]})
        used_models.append(model)
        used_families.append(family(model))
        if answer["verdict"] != "approve":
            return {"status": "held", "reason": "reviewer_rejected", "votes": votes}
    body = {"status": "approved", "votes": votes, "author_model": author_model,
            "coverage": coverage, "content_digest": content_digest(files)}
    body["digest"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return body
