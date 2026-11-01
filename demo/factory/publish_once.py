"""Worker-side publish preparation: build, gate, review, then queue. Never holds a publish key.

This process can run with the inference credential only. It produces a reviewed request and
stops; `factory/publisher.py` is the single process allowed to hold the GitHub credential and
turn that request into a branch and a pull request.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from factory.api import S2_CONFIG
from factory.dispatch import DispatchWorker
from factory.keys import assert_worker_isolated
from factory.manifest import load_manifest
from factory.store import Store

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="OualidGuennif/aeion-autonomous-forum")
    parser.add_argument("--base", default="develop")
    parser.add_argument("--feature", default="001")
    parser.add_argument("--state", default=str(ROOT / "demo/.local/factory/publish-real"))
    parser.add_argument("--manifest", default=str(ROOT / "demo/forum/features/MANIFEST.json"))
    parser.add_argument("--specs", default=str(ROOT / "demo/forum/features"))
    parser.add_argument("--author-model", default="deepseek-4.1-flash")
    args = parser.parse_args(argv)

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
    worker = DispatchWorker(store, catalog, Path(args.specs), state / "work", S2_CONFIG,
                            target_repo=args.repo, defer_to=state,
                            review_complete=open_code_complete, author_model=args.author_model)
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
