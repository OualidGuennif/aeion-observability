#!/usr/bin/env python3
"""Verify that a feature is already present in the pinned product base, then record it.

A baseline is evidence, not a simulated build: the required paths are hashed from the
exact pinned commit and the base test suite runs in the same isolated Docker check used
for candidates. Only a passing check can be recorded, and only for the pinned base sha.
Dependencies then treat that feature as satisfied without pretending a build ran.
"""
import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
REPO = DEMO.parent
sys.path.insert(0, str(DEMO))
from factory.checks import _failed_tests
from factory.isolation import DockerCheckRunner
from factory.manifest import load_manifest
from factory.store import Store
from factory.target import TargetError, load_target

BASELINE_FEATURES = {
    "001": {
        "paths": [
            "demo/forum-app/build.gradle",
            "demo/forum-app/settings.gradle",
            "demo/forum-app/src/main/resources/application.properties",
            "demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java",
            "demo/forum-app/src/main/java/local/aeion/forum/Setting.java",
        ],
        "description": "app skeleton, typed settings and /healthz at the pinned base",
    },
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(feature_id, target, runner, work_root=None):
    spec = BASELINE_FEATURES[feature_id]
    if work_root is not None:
        Path(work_root).mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"aeion-baseline-{feature_id}-",
                                     dir=str(work_root) if work_root is not None else None) as folder:
        repo = Path(folder) / "repo"
        target.materialize(repo)
        missing = [path for path in spec["paths"] if not (repo / path).is_file()]
        if missing:
            raise SystemExit("baseline paths missing: " + json.dumps(missing))
        command = target.protected_check.command_for(repo, target.controller)
        completed = runner(command, cwd=str(repo), timeout=target.protected_check.timeout_seconds)
        if completed.returncode != 0:
            failed = _failed_tests((getattr(completed, "stdout", "") or "")
                                   + "\n" + (getattr(completed, "stderr", "") or ""))
            raise SystemExit("baseline test suite failed: returncode="
                             + str(completed.returncode) + " failed=" + json.dumps(failed[:10]))
        evidence = {
            "kind": "pinned_base_baseline",
            "feature_id": feature_id,
            "description": spec["description"],
            "base_sha": target.base_sha,
            "paths": {path: digest(repo / path) for path in spec["paths"]},
            "check": {
                "id": target.protected_check.id,
                "returncode": completed.returncode,
                "duration_ms": getattr(completed, "duration_ms", None),
                "isolation": getattr(completed, "qualification", None),
            },
            "verifier": "demo/factory/baseline.py",
            "verified_at_ns": time.time_ns(),
        }
    isolation = evidence["check"]["isolation"]
    if not isolation or isolation.get("status") != "qualified":
        raise SystemExit("baseline check did not run under a qualified boundary")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature", default="001", choices=sorted(BASELINE_FEATURES))
    parser.add_argument("--target", default=str(REPO / "demo/forum/targets/forum-app-013.json"))
    parser.add_argument("--state", default=str(DEMO / ".local/factory"))
    parser.add_argument("--apply", action="store_true",
                        help="record the verified baseline in the factory store")
    args = parser.parse_args()

    target = load_target(args.target, REPO)
    catalog = load_manifest(REPO / "demo/forum/features/MANIFEST.json")
    if args.feature not in catalog.by_id:
        raise SystemExit("unknown feature: " + args.feature)
    runner = DockerCheckRunner(REPO)
    state = Path(args.state)
    evidence = verify(args.feature, target, runner, work_root=state / "work")
    output = {"evidence": evidence, "applied": None}
    if args.apply:
        state.mkdir(parents=True, exist_ok=True)
        store = Store(state / "factory.db")
        output["applied"] = store.record_baseline(args.feature, evidence, catalog)
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
