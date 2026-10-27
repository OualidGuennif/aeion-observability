"""Small, strict native-usage boundary; telemetry never controls admission."""
from decimal import Decimal, InvalidOperation


def native_usage(usage):
    # Flue/Pi turn usage: `input` excludes cache reads/writes; `output` includes reasoning.
    if not isinstance(usage, dict):
        raise ValueError("USAGE_UNKNOWN")
    values = [usage.get("input"), usage.get("cacheRead"), usage.get("cacheWrite"), usage.get("output")]
    if any(type(v) is not int or v < 0 for v in values) or sum(values[:3]) == 0:
        raise ValueError("USAGE_UNKNOWN")
    cost = usage.get("cost")
    if type(cost) not in (int, float):
        raise ValueError("COST_UNKNOWN")
    try:
        cost = Decimal(str(cost))
    except InvalidOperation:
        raise ValueError("COST_UNKNOWN") from None
    if not cost.is_finite() or cost < 0:
        raise ValueError("COST_UNKNOWN")
    return {"input": sum(values[:3]), "output": values[3], "cost": cost}


def gate_value(usage, cumulative, metric):
    if metric not in {"active_context", "cumulative_input"}:
        raise ValueError("INVALID_METRIC")
    return usage["input"] if metric == "active_context" else cumulative
