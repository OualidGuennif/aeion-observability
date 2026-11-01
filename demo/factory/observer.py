"""Observer: bounded, deduplicated observations of completed builds.

Watches the board for builds in an awaiting-observation status and emits a compact
proposal once each, persisted so a restart never re-proposes the same build. Metadata
is bounded on purpose: no receipt bodies, no spec text, only identity, status and the
artifact digest the gate already recorded.
"""
import json
import time

from .store import SIMULATED_COMPLETE


class Observer:
    def __init__(self, store, statuses=(SIMULATED_COMPLETE,), max_batch=100):
        self.store = store
        self.statuses = tuple(statuses)
        self.max_batch = int(max_batch)
        self._seen = set()

    def propose(self, actor="observer"):
        proposals = []
        now = time.time_ns()
        for build in self.store.board():
            if build["status"] not in self.statuses:
                continue
            key = f"observer:proposed:{build['build_id']}"
            if key in self._seen:
                continue
            if self.store.meta_get(key) is not None:
                self._seen.add(key)
                continue
            digest = None
            if build.get("receipt"):
                try:
                    digest = json.loads(build["receipt"]).get("artifact_digest")
                except (ValueError, TypeError):
                    digest = None
            proposal = {
                "build_id": build["build_id"],
                "feature_id": build["feature_id"],
                "status": build["status"],
                "artifact_digest": digest,
                "proposed_ns": now,
            }
            self.store.meta_set(key, json.dumps(proposal, sort_keys=True, separators=(",", ":")))
            self._seen.add(key)
            proposals.append(proposal)
            if len(proposals) >= self.max_batch:
                break
        return proposals
