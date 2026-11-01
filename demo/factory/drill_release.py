#!/usr/bin/env python3
"""A compressed end-to-end drill: build → stage → validate → 25% → 50% → 100%, with real traffic.

The dwells are compressed by `--scale` and the factor is written on the release, so this drill can
never be read as a six-hour canary. Everything else is the real path: the worker, the gate, the
two-model circuit, the balancer, the cache, the samples and the gate verdict.

    python3 demo/factory/drill_release.py --redis redis://127.0.0.1:6399
"""
import argparse
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEMO))

from deploy.cache import connect  # noqa: E402
from deploy.playground import Playground  # noqa: E402
from factory import canary, release  # noqa: E402
from factory.dispatch import DispatchWorker  # noqa: E402
from factory.manifest import Catalog  # noqa: E402
from factory.releases import ReleaseService  # noqa: E402
from factory.store import SIMULATED_COMPLETE, Store  # noqa: E402

CONFIG = {"profile": "fake", "mode": "fake", "deadline_ns": 300 * 1_000_000_000,
          "step_cap": 200, "context_limit": 250_000, "cost_reservation_usd": "0.00"}
HOUR_NS = 3600 * 1_000_000_000


def deterministic_answer(model, prompt):
    return {"verdict": "approve", "reason": f"simulated review by {model}"}


def traffic(playground, count, client="drill-agent"):
    seen = {}
    for index in range(count):
        request = urllib.request.Request(
            f"http://127.0.0.1:{playground.port}/api/threads",
            headers={"X-Client": f"{client}-{index % 7}"})
        try:
            with urllib.request.urlopen(request) as response:
                response.read()
                seen[response.headers["X-Aeion-Slot"]] = seen.get(response.headers["X-Aeion-Slot"], 0) + 1
        except urllib.error.HTTPError as exc:
            exc.close()
    return seen


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", nargs="+", default=["001", "002", "003"])
    parser.add_argument("--redis", default=None)
    parser.add_argument("--scale", type=float, default=1 / 3600, help="1/3600 turns 6 h into 6 s")
    parser.add_argument("--state", default=None)
    parser.add_argument("--sample-seconds", type=float, default=0)
    args = parser.parse_args(argv)

    state_dir = Path(args.state) if args.state else Path(tempfile.mkdtemp(prefix="aeion-drill-"))
    if state_dir.exists() and args.state is None:
        shutil.rmtree(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest = DEMO / "forum/features/MANIFEST.json"
    catalog = Catalog(json.loads(manifest.read_text()))
    store = Store(state_dir / "factory.db", simulated_dependencies=True)

    worker = DispatchWorker(store, catalog, manifest.parent, state_dir / "work", config=CONFIG,
                            defer_to=state_dir, review_complete=deterministic_answer,
                            require_circuit=True)
    for feature_id in args.features:
        store.admit([feature_id], f"drill-{feature_id}", catalog, actor="operator")
        worker.run_once()

    board = {row["feature_id"]: row for row in store.board()}
    built = [{"id": fid, "title": catalog.by_id[fid]["title"],
              "digest": json.loads(board[fid]["receipt"])["artifact_digest"]}
             for fid in args.features if board[fid]["status"] == SIMULATED_COMPLETE]
    if len(built) != len(args.features):
        raise SystemExit(f"not every feature built: {sorted(board)}")

    cache, backend = connect(args.redis, state_dir / "cache", ttl=120)
    playground = Playground(cache, percent=0, seed="drill").start()
    now = [1_700_000_000_000_000_000]
    service = ReleaseService(store, playground, state_dir / "releases", scale=args.scale,
                             clock=lambda: now[0], sample_interval_seconds=args.sample_seconds)
    steps = []
    try:
        record = service.stage(built, flags={"dark_mode": {"enabled": True, "rollout": 25}},
                               now=now[0])
        steps.append({"event": "staged", "state": record["state"], "percent": record["percent"]})

        record = service.validate(now=now[0])
        routed = traffic(playground, 140)
        steps.append({"event": "validated", "percent": record["percent"], "routed": routed,
                      "cache_backend": backend})

        for target in (50, 100):
            now[0] += 7 * HOUR_NS
            # The monitor needs four samples with traffic before it will say "continue".
            for _ in range(4):
                traffic(playground, 20)
                service.tick(now=now[0])
                now[0] += 1_000_000_000
            record = service.current()
            if record["state"] == release.STATE_CANARY and record["percent"] < target:
                record = service.advance(now=now[0])
            routed = traffic(playground, 140)
            steps.append({"event": f"advanced_to_{record['percent']}", "state": record["state"],
                          "routed": routed, "gate": service.gate(record)["verdict"]})
        summary = {
            "ok": record["state"] == release.STATE_RELEASED,
            "release_id": record["release_id"],
            "state": record["state"],
            "percent": record["percent"],
            "scale": record["scale"],
            "cache_backend": backend,
            "steps": steps,
            "traffic": playground.stats(),
            "samples": canary.summarise(service._samples(record["release_id"])),
            "flags": record["flags"],
        }
    finally:
        playground.stop()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
