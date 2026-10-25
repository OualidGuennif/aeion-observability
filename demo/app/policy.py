"""Small, strict native-usage boundary; telemetry never controls admission."""
from decimal import Decimal, InvalidOperation


def native_usage(part):
    tokens = part.get("tokens", {})
    cache = tokens.get("cache", {})
    values = [tokens.get("input"), cache.get("read"), cache.get("write"),
              tokens.get("output"), tokens.get("reasoning")]
    if any(type(v) is not int or v < 0 for v in values) or sum(values[:3]) == 0:
        raise ValueError("USAGE_UNKNOWN")
    try:
        cost = Decimal(str(part["cost"]))
    except (KeyError, InvalidOperation):
        raise ValueError("COST_UNKNOWN") from None
    if not cost.is_finite() or cost < 0:
        raise ValueError("COST_UNKNOWN")
    return {"input": sum(values[:3]), "output": values[3] + values[4], "cost": cost}


def gate_value(usage, cumulative, metric):
    if metric not in {"active_context", "cumulative_input"}:
        raise ValueError("INVALID_METRIC")
    return usage["input"] if metric == "active_context" else cumulative
