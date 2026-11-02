"""Worker-side publish preparation: build, gate, review, then queue. Never holds a publish key.

This process can run with the inference credential only. It produces a reviewed request and
stops; `factory/publisher.py` is the single process allowed to hold the GitHub credential and
turn that request into a branch and a pull request.
"""
import argparse
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from factory.api import S2_CONFIG
from factory.budget import DailyBudget
from factory.dispatch import DispatchWorker
from factory.keys import assert_worker_isolated
from factory.manifest import load_manifest
from factory.store import Store

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = Path(os.environ.get("AEION_BUDGET_LEDGER")
                      or ROOT / "demo/.local/budget/ledger.jsonl")


def positive_reservation(value):
    """A paid worker may not reserve zero; the purse would never see the review spend."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("invalid_cost_reservation") from None
    if not amount.is_finite() or amount < Decimal("0.01"):
        raise ValueError("invalid_cost_reservation")
    return format(amount, "f")


def build_worker(store, catalog, spec_dir, state, target_repo, author_model,
                 review_complete, cost_reservation_usd, ledger=None):
    """Wire the paid publish worker to the shared forum purse before it can reach a model."""
    config = {**S2_CONFIG, "cost_reservation_usd": cost_reservation_usd}
    return DispatchWorker(
        store, catalog, Path(spec_dir), Path(state) / "work", config,
        target_repo=target_repo, defer_to=Path(state),
        review_complete=review_complete, author_model=author_model,
        budget=DailyBudget(Path(ledger) if ledger is not None else DEFAULT_LEDGER),
        budget_scope="aeion-autonomous-forum",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="OualidGuennif/aeion-autonomous-forum")
    parser.add_argument("--base", default="develop")
    parser.add_argument("--feature", default="001")
    parser.add_argument("--state", default=str(ROOT / "demo/.local/factory/publish-real"))
    parser.add_argument("--manifest", default=str(ROOT / "demo/forum/features/MANIFEST.json"))
    parser.add_argument("--specs", default=str(ROOT / "demo/forum/features"))
    parser.add_argument("--author-model", default="deepseek-4.1-flash")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER),
                        help="the shared daily budget journal")
    parser.add_argument("--cost-reservation-usd", default="0.10",
                        help="positive per-build reservation charged to aeion-autonomous-forum")
    args = parser.parse_args(argv)
    try:
        reservation = positive_reservation(args.cost_reservation_usd)
    except ValueError:
        parser.error("--cost-reservation-usd must be a positive finite amount")

    # A worker must not hold the credential that can publish or merge.
    try:
        assert_worker_isolated()
    except Exception as exc:  # noqa: BLE001 - report, never continue
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 2

    from factory.model_client import open_code_complete

    catalog = load_manifest(Path(args.manifest))
    state = Path(args.state)
    store = Store(state / "factory.db")
    worker = build_worker(store, catalog, Path(args.specs), state, args.repo,
                          args.author_model, open_code_complete, reservation, args.ledger)
    out = {"repo": args.repo, "base": args.base, "feature": args.feature, "mode": "deferred",
           "author_model": args.author_model}
    admission = store.admit([args.feature], f"defer-{args.feature}-{args.base}", catalog)
    out["admission"] = admission["status"]
    result = worker.run_once()
    out["worker"] = result
    build = next((b for b in store.board() if b["build_id"] == (result or {}).get("build_id")), None)
    out["status"] = build["status"] if build else None
    out["hold_reason"] = build["hold_reason"] if build else None
    if build and build.get("receipt"):
        receipt = json.loads(build["receipt"])
        out["gate"] = (receipt.get("gate") or {}).get("status")
        out["review"] = (receipt.get("review") or {}).get("status")
        circuit = receipt.get("circuit") or {}
        out["circuit"] = circuit.get("status")
        out["circuit_models"] = [v.get("model") for v in circuit.get("votes", [])]
        out["publisher"] = (receipt.get("publisher") or {}).get("decision")
    out["queued"] = sorted(p.name for p in (state / "publish-queue").glob("*.json")) \
        if (state / "publish-queue").is_dir() else []
    out["ok"] = bool(out["queued"])
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
