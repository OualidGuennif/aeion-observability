#!/usr/bin/env python3
"""Recompute the bundled fictional cohort example; never call a provider or change a session.

Spec: knowledge/operations/quality-and-evaluation.md
"""

from decimal import Decimal, InvalidOperation
import json
from math import ceil
from pathlib import Path


def summarize(data):
    """Summarize complete synthetic task costs, preserving unknown quality and undefined ratios."""
    if data.get("example_only") is not True or data.get("currency") != "USD":
        raise ValueError("This demonstration accepts only the synthetic USD fixture format")
    rows = []
    policy_ids = set()
    cohort_ids = None
    for policy in data["policies"]:
        if policy["policy_id"] in policy_ids:
            raise ValueError("Duplicated policy identity")
        policy_ids.add(policy["policy_id"])
        tasks = policy["tasks"]
        task_ids = {t["task_id"] for t in tasks}
        if not tasks or len(task_ids) != len(tasks):
            raise ValueError("Empty cohort or duplicated task identity")
        if cohort_ids is None:
            cohort_ids = task_ids
        elif task_ids != cohort_ids:
            raise ValueError("Compared policies must contain the same task identities")
        total = Decimal(0)
        for task in tasks:
            if task["outcome"] not in {"autonomous", "assisted", "failed", "unknown"}:
                raise ValueError("Unknown outcome label")
            for key in ("request_count", "wall_seconds", "corrective_minutes"):
                if type(task[key]) is not int or task[key] < 0:
                    raise ValueError("Invalid nonnegative task measurement")
            if task["outcome"] == "autonomous" and task["corrective_minutes"] != 0:
                raise ValueError("An autonomous success cannot include corrective human work")
            if set(task["costs"]) != {"inference", "sandbox", "evaluation", "observability"}:
                raise ValueError("The example requires every declared cost category")
            for value in task["costs"].values():
                if not isinstance(value, str):
                    raise ValueError("Money values must be decimal strings")
                try:
                    amount = Decimal(value)
                except InvalidOperation as error:
                    raise ValueError("Cost must be a decimal string") from error
                if not amount.is_finite() or amount < 0:
                    raise ValueError("Cost must be finite and nonnegative")
                total += amount
        quality_known = all(t.get("maturity") == "mature" and t.get("intervention_coverage") == "complete"
                            and t["outcome"] != "unknown" for t in tasks)
        successes = sum(t["outcome"] == "autonomous" for t in tasks) if quality_known else None
        durations = sorted(t["wall_seconds"] for t in tasks)
        rows.append({"policy_id": policy["policy_id"], "synthetic": True,
                     "cohort_cost_usd": str(total), "task_count": len(tasks),
                     "verified_autonomous_successes": successes,
                     "cost_per_autonomous_success_usd": str(total / successes) if successes else None,
                     "p95_wall_seconds_nearest_rank": durations[ceil(0.95 * len(durations)) - 1],
                     "quality_evidence": "synthetic_complete" if quality_known else "unknown"})
    return rows


def main():
    path = Path(__file__).with_name("cohort-comparison.json")
    rows = summarize(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps({"example_only": True, "not_a_benchmark": True, "policies": rows}, indent=2))


if __name__ == "__main__":
    main()
