"""Model registry and telemetry-driven routing for the review circuit.

The circuit must never let the model that wrote the code vote on it, and the two votes must
come from different model families. This module only *names* models and scores them; it makes
no call and holds no credential. Selection is deterministic for a given telemetry snapshot, so
a decision can be reproduced and audited.
"""
import math

# One family per vendor: two models of the same family share weights and failure modes.
MODELS = {
    "claude-haiku-5.5": {"family": "anthropic", "cost": 4.0, "quality": 0.95, "roles": {"review", "author"}},
    "deepseek-4.1-flash": {"family": "deepseek", "cost": 1.0, "quality": 0.80, "roles": {"review", "author"}},
    "qwen-3.8-flash": {"family": "qwen", "cost": 0.9, "quality": 0.78, "roles": {"review", "author"}},
    "glm-5.3-flash": {"family": "zhipu", "cost": 0.8, "quality": 0.78, "roles": {"review", "author"}},
}
DEFAULT_REVIEW_ORDER = ("glm-5.3-flash", "qwen-3.8-flash", "deepseek-4.1-flash", "claude-haiku-5.5")
MAX_RECORDS = 500


class RoutingError(ValueError):
    """No eligible model for a request."""


def family(model):
    return MODELS[model]["family"]


def known(model):
    return model in MODELS


class Telemetry:
    """Bounded record of what each model actually did; the router's only input."""

    def __init__(self, max_records=MAX_RECORDS):
        self.max_records = int(max_records)
        self.records = []

    def record(self, model, purpose, outcome, latency_ms=None, cost_usd=None):
        if not known(model):
            raise RoutingError(f"unknown_model:{model}")
        self.records.append({"model": model, "purpose": purpose, "outcome": outcome,
                             "latency_ms": latency_ms, "cost_usd": cost_usd})
        if len(self.records) > self.max_records:
            del self.records[: len(self.records) - self.max_records]

    def stats(self, model, purpose=None):
        rows = [r for r in self.records if r["model"] == model and (purpose is None or r["purpose"] == purpose)]
        if not rows:
            return {"n": 0, "success_rate": None, "avg_latency_ms": None, "avg_cost_usd": None}
        ok = sum(1 for r in rows if r["outcome"] in {"approved", "rejected", "passed"})
        latencies = [r["latency_ms"] for r in rows if isinstance(r["latency_ms"], (int, float))]
        costs = [r["cost_usd"] for r in rows if isinstance(r["cost_usd"], (int, float))]
        return {
            "n": len(rows),
            "success_rate": ok / len(rows),
            "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
            "avg_cost_usd": (sum(costs) / len(costs)) if costs else None,
        }


class Router:
    """Choose the most efficient eligible model, never a family already used in this review."""

    def __init__(self, telemetry=None, models=None):
        self.telemetry = telemetry or Telemetry()
        self.models = dict(models or MODELS)

    def score(self, model, purpose):
        spec = self.models[model]
        stats = self.telemetry.stats(model, purpose)
        # Efficiency: expected quality per unit of cost, penalised by measured failures and
        # latency. Unknown models score on their declared priors only.
        reliability = stats["success_rate"] if stats["success_rate"] is not None else 0.9
        latency_penalty = 0.0
        if stats["avg_latency_ms"]:
            latency_penalty = min(0.2, math.log10(1 + stats["avg_latency_ms"] / 1000) / 20)
        return (spec["quality"] * reliability) / spec["cost"] - latency_penalty

    def select(self, purpose="review", exclude_models=(), exclude_families=(), require_role=None):
        blocked_models = set(exclude_models)
        blocked_families = set(exclude_families)
        candidates = []
        for model, spec in self.models.items():
            if model in blocked_models or spec["family"] in blocked_families:
                continue
            if require_role and require_role not in spec["roles"]:
                continue
            candidates.append(model)
        if not candidates:
            raise RoutingError("no_eligible_model")
        return max(candidates, key=lambda m: (round(self.score(m, purpose), 6), m))


def eligible(models=None, exclude_models=(), exclude_families=()):
    blocked_models, blocked_families = set(exclude_models), set(exclude_families)
    return sorted(m for m, spec in (models or MODELS).items()
                  if m not in blocked_models and spec["family"] not in blocked_families)
