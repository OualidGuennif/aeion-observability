"""Descriptive task-level KPIs. Include failed attempts; separate synthetic evidence."""
from collections import defaultdict
from decimal import Decimal
from statistics import median


def summarize(runs):
    groups = defaultdict(list)
    for run in runs:
        key = (run.get("task_id", "pricing-js-v1"), run["synthetic"], "synthetic-replay" if run["synthetic"] else run["model"], run["metric"], run["limit"], run.get("profile_version", "unversioned"))
        groups[key].append(run)
    rows = []
    for (task_id, synthetic, model, metric, limit, version), cohort in groups.items():
        completed = [r for r in cohort if r.get("ended_ns")]
        autonomous = [r for r in completed if r["status"] == "passed" and r.get("human_interventions", 0) == 0]
        durations = [(r["ended_ns"] - r["started_ns"]) / 1000000 for r in completed]
        usages = [e for r in cohort for e in r["events"] if e["name"] == "gen_ai.request"]
        cost = sum((Decimal(r["native_cost_usd"]) for r in cohort), Decimal(0))
        complete_cost = all(r.get("usage_complete", False) and r.get("ended_ns") for r in cohort)
        rows.append({
            "task_id": task_id, "synthetic": synthetic, "model": model, "metric": metric, "limit": limit, "profile_version": version,
            "offered": len(cohort), "completed": len(completed), "pending": len(cohort) - len(completed),
            "passed": sum(r["status"] == "passed" for r in completed), "autonomous": len(autonomous),
            "autonomous_rate": len(autonomous) / len(completed) if completed else None,
            "median_ms": round(median(durations), 2) if durations else None,
            "input_tokens": sum(e["gen_ai.usage.input_tokens"] for e in usages),
            "output_tokens": sum(e["gen_ai.usage.output_tokens"] for e in usages),
            "cli_cost_estimate_usd": str(cost),
            "cost_per_autonomous_success_usd": str(cost / len(autonomous)) if autonomous and complete_cost else None,
            "usage_complete": complete_cost,
            "accounting_basis": "synthetic" if synthetic else "cli_estimate_not_invoice",
            "evidence": "demo_fixture_only",
        })
    return rows
