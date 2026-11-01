#!/usr/bin/env python3
"""Run real features through the factory and stage them as one release.

This is the operator's entry point for "build these features and put them in staging". It uses the
same worker, gate, reviewer and circuit as the cockpit, writes to the same state directory, and
never touches GitHub: publishing stays a separate, credential-holding process.

Inference is simulated unless `--live` is passed. The receipts say `simulated: true`, so a run of
this script is never evidence that a model reviewed anything — only that the mechanics hold.

    python3 demo/factory/run_features.py --features 001 002 003
"""
import argparse
import json
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEMO))

from deploy.cache import connect  # noqa: E402
from deploy.playground import Playground  # noqa: E402
from factory.dispatch import DispatchWorker  # noqa: E402
from factory.manifest import Catalog  # noqa: E402
from factory.model_client import complete  # noqa: E402
from factory.releases import ReleaseService  # noqa: E402
from factory.store import SIMULATED_COMPLETE, Store  # noqa: E402

CONFIG = {"profile": "fake", "mode": "fake", "deadline_ns": 300 * 1_000_000_000,
          "step_cap": 200, "context_limit": 250_000, "cost_reservation_usd": "0.00"}


def deterministic_answer(model, prompt):
    """A stand-in reviewer: it answers like a model, deterministically, and says so in the receipt."""
    return {"verdict": "approve", "reason": f"simulated review by {model}"}


def live_answer(model, prompt):
    return complete(model, prompt)


def build(store, catalog, spec_dir, state_dir, features, review_complete):
    worker = DispatchWorker(store, catalog, spec_dir, state_dir / "work", config=CONFIG,
                            defer_to=state_dir, review_complete=review_complete,
                            require_circuit=True)
    results = []
    for feature_id in features:
        built_already = [row for row in store.board()
                         if row["feature_id"] == feature_id and row["status"] == SIMULATED_COMPLETE]
        if built_already:
            results.append({"feature": feature_id, "outcome": {"result": {"status": "already_built"}}})
            continue
        store.admit([feature_id], f"run-{feature_id}-{len(store.board())}", catalog, actor="operator")
        outcome = worker.run_once()
        results.append({"feature": feature_id, "outcome": outcome})
    return results


def staged_features(store, catalog, features):
    board = {row["feature_id"]: row for row in store.board()}
    built = []
    for feature_id in features:
        row = board.get(feature_id)
        if not row or row["status"] != SIMULATED_COMPLETE or not row.get("receipt"):
            raise SystemExit(f"feature {feature_id} did not reach a built state: "
                             f"{row['status'] if row else 'missing'}")
        receipt = json.loads(row["receipt"])
        title = catalog.by_id[feature_id]["title"] if feature_id in catalog.by_id else feature_id
        built.append({"id": feature_id, "title": title,
                      "digest": receipt["artifact_digest"]})
    return built


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", nargs="+", default=["001", "002", "003"])
    parser.add_argument("--state", default=str(DEMO / ".local/factory"))
    parser.add_argument("--live", action="store_true", help="use the real review endpoint")
    parser.add_argument("--flags", default='{"dark_mode": {"enabled": true, "rollout": 20}}')
    args = parser.parse_args(argv)

    state_dir = Path(args.state)
    manifest = DEMO / "forum/features/MANIFEST.json"
    catalog = Catalog(json.loads(manifest.read_text()))
    store = Store(state_dir / "factory.db", simulated_dependencies=True)

    review_complete = live_answer if args.live else deterministic_answer
    results = build(store, catalog, manifest.parent, state_dir, args.features, review_complete)
    built = staged_features(store, catalog, args.features)

    cache, backend = connect(None, state_dir / "cache", ttl=60)
    playground = Playground(cache, percent=0, seed="staged")
    service = ReleaseService(store, playground, state_dir / "releases")
    record = service.stage(built, flags=json.loads(args.flags))
    print(json.dumps({
        "ok": True,
        "features": built,
        "release_id": record["release_id"],
        "state": record["state"],
        "percent": record["percent"],
        "cache_backend": backend,
        "runs": [{"feature": r["feature"],
                  "status": (r["outcome"] or {}).get("result", {}).get("status")} for r in results],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
