"""Model registry and telemetry-driven routing for the review circuit.

The circuit must never let the model that wrote the code vote on it, and the two votes must
come from different model families. This module only *names* models and scores them; it makes
no call and holds no credential. Selection is deterministic for a given telemetry snapshot, so
a decision can be reproduced and audited.

This catalog is also the one eligibility authority for the owner-authorized workers:
``demo/app/profiles.py`` asks it for availability instead of keeping a second expiry, and the
live client refuses an ineligible model before transport. A spend approval is not a provider
requalification: a recorded profile expiry stays binding, so an expired harness qualification
cannot be carried by the authorization date.
"""
import datetime

# One family per vendor: two models of the same family share weights and failure modes.
# The display id stays internal; ``wire`` is the provider's documented identifier and is the
# only value sent on the wire. The owner authorized these four workers on 2026-11-02; that
# authorization is not a provider requalification, and no ZDR claim is made for any of them.
OWNER_AUTHORIZATION = "2026-11-02"
MODELS = {
    "claude-haiku-5.5": {"family": "anthropic", "wire": "claude-haiku-5-5",
                         "roles": {"review", "author"}, "retention_days": 30,
                         "authorization": OWNER_AUTHORIZATION},
    "deepseek-4.1-flash": {"family": "deepseek", "wire": "deepseek-v4.1-flash",
                           "roles": {"review", "author"},
                           "authorization": OWNER_AUTHORIZATION, "profile": "deepseek",
                           "profile_expires": "2026-11-30"},
    "qwen-3.8-flash": {"family": "qwen", "wire": "qwen3.8-flash",
                       "roles": {"review", "author"},
                       "authorization": OWNER_AUTHORIZATION},
    "glm-5.3-flash": {"family": "zhipu", "wire": "glm-5.3-flash",
                      "roles": {"review", "author"},
                      "authorization": OWNER_AUTHORIZATION, "profile": "glm"},
    # Added by the owner on 2026-11-06.
    "gpt-6-luna": {"family": "openai", "wire": "gpt-6-luna",
                   "roles": {"review", "author"}, "retention_days": 30,
                   "authorization": "2026-11-06"},
    # Owner request 2026-11-08: MiniMax M3.1 Flash replaces Mistral Large 4.
    "minimax-m3.1-flash": {"family": "minimax", "wire": "minimax-m3.1-flash",
                           "roles": {"review", "author"},
                           "authorization": "2026-11-08"},
}
# New models follow the measured ones in the cold-start order until telemetry ranks them.
DEFAULT_REVIEW_ORDER = ("glm-5.3-flash", "qwen-3.8-flash", "deepseek-4.1-flash", "claude-haiku-5.5",
                        "gpt-6-luna", "minimax-m3.1-flash")
MAX_RECORDS = 500


class RoutingError(ValueError):
    """No eligible model for a request."""


def family(model):
    return MODELS[model]["family"]


def known(model):
    return model in MODELS


def eligibility(model, today=None):
    """Return ``(eligible, reason)`` from the catalog's authorization and profile facts.

    Unknown models and missing authorization fail closed. A recorded profile expiry is binding
    even after the owner authorization: the harness qualification is the thing that expired,
    and a spend decision does not renew it.
    """
    spec = MODELS.get(model)
    if spec is None:
        return False, "unknown_model"
    if not spec.get("authorization"):
        return False, "authorization_missing"
    day = today or datetime.date.today().isoformat()
    if day < spec["authorization"]:
        return False, "authorization_not_yet_valid"
    expires = spec.get("profile_expires")
    if expires and day > expires:
        return False, "profile_expired"
    return True, None


def wire_id(model):
    """The documented provider identifier for an internal display id."""
    try:
        return MODELS[model]["wire"]
    except KeyError:
        raise RoutingError(f"unknown_model:{model}") from None


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


# One paid request reserves its whole output window plus a minimal input at the model's budget
# rate (list price times the measured allowance multiple). A model whose single request already
# costs more than half of its purpose's cap cannot finish within it: Claude Haiku 5.5 at 4x is
# about 0.70 USD per 65536-token review request against a 1 USD vote. Such a model is not selected.
PURPOSE_OUTPUT_TOKENS = {"author": 65536, "review": 65536, "prepare": 32768}
PREPARE_CAP_USD = "0.50"


def request_floor_usd(model, purpose):
    from decimal import Decimal
    from app.profiles import PROFILES, SHARED_MODELS, budget_multiplier
    key = next(k for k, v in SHARED_MODELS.items() if v == model)
    profile = PROFILES[key]
    rate = max(Decimal(str(profile["input"])), Decimal(str(profile.get("cache_write", 0))))
    return ((Decimal(PURPOSE_OUTPUT_TOKENS[purpose]) * Decimal(str(profile["output"])) + 16384 * rate)
            * Decimal(budget_multiplier(key)) / 1000000)


def fits_budget(model, purpose):
    """Unknown price, multiple or cap means no: fail closed."""
    from decimal import Decimal
    try:
        if purpose == "prepare":
            cap = Decimal(PREPARE_CAP_USD)
        else:
            from .budget import settings
            cap = settings()["AUTHOR_MAX_USD" if purpose == "author" else "REVIEW_MAX_USD"]
        return request_floor_usd(model, purpose) <= cap / 2
    except Exception:
        return False


class Router:
    """Choose the most efficient eligible model, never a family already used in this review."""

    def __init__(self, telemetry=None, models=None):
        self.telemetry = telemetry or Telemetry()
        self.models = dict(models or MODELS)

    def score(self, model, purpose):
        stats = self.telemetry.stats(model, purpose)
        # Cold start is an explicit fixed preference, not an invented quality/price estimate.
        # Actual protocol/check failures can demote that preference before cost ranking has
        # enough complete comparable samples. Missing evidence supplies no measured score.
        order = DEFAULT_REVIEW_ORDER.index(model)
        failure_rate = 1 - stats['success_rate'] if stats['success_rate'] is not None else 0
        return -order - 100 * failure_rate

    def select(self, purpose="review", exclude_models=(), exclude_families=(), require_role=None):
        blocked_models = set(exclude_models)
        blocked_families = set(exclude_families)
        candidates = []
        for model, spec in self.models.items():
            if model in blocked_models or spec["family"] in blocked_families:
                continue
            if require_role and require_role not in spec["roles"]:
                continue
            if not eligibility(model)[0] or not fits_budget(model, purpose):
                continue
            candidates.append(model)
        if not candidates:
            raise RoutingError("no_eligible_model")
        statistics = {m: self.telemetry.stats(m, purpose) for m in candidates}
        measured = [m for m, stats in statistics.items() if stats['n'] >= 3
                    and stats.get('usage_complete') and stats.get('outcomes_complete') and stats.get('latency_complete')
                    and stats['avg_cost_usd'] is not None and stats['avg_latency_ms'] is not None]
        basis = 'cold_start_prior'
        scores = {m: round(self.score(m, purpose), 6) for m in candidates}
        if len(measured) >= 2:
            basis = 'measured_cost_latency'
            # Equal relative cost/time weights, with observed protocol/check failure penalty.
            # Decimal spend is preserved in storage; these dimensionless scores are advisory.
            cost_min = max(0.000001, min(statistics[m]['avg_cost_usd'] for m in measured))
            time_min = max(1, min(statistics[m]['avg_latency_ms'] for m in measured))
            scores = {m: round(statistics[m]['success_rate'] /
                (1 + statistics[m]['avg_cost_usd'] / cost_min
                   + statistics[m]['avg_latency_ms'] / time_min), 9) for m in measured}
        selected = max(scores, key=lambda m: (scores[m], m))
        self.last_decision = {'basis': basis, 'purpose': purpose, 'model': selected,
                             'cohort': getattr(self.telemetry, 'cohort', None), 'scores': scores,
                             'samples': {m: statistics[m]['n'] for m in scores}}
        return selected


def eligible(models=None, exclude_models=(), exclude_families=()):
    """The public list of selectable models; an ineligible profile is never listed."""
    blocked_models, blocked_families = set(exclude_models), set(exclude_families)
    return sorted(m for m, spec in (models or MODELS).items()
                  if m not in blocked_models and spec["family"] not in blocked_families
                  and eligibility(m)[0])


def author_model(telemetry=None, exclude_models=(), exclude_families=()):
    """The shared, explainable choice for an authoring call; never a reviewer's vote."""
    return Router(telemetry).select("author", exclude_models=exclude_models,
                                    exclude_families=exclude_families, require_role="author")
