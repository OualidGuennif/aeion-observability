"""Fake builder: honest dry-run execution producing a clearly simulated receipt.

It claims queued work from the store, writes a disposable fake diff and returns a
receipt that is visibly labelled simulated. No inference, network or paid call occurs.
"""
import hashlib
import time
from pathlib import Path


class FakeWorker:
    def __init__(self, store, catalog, work_root, delay=0.1):
        self.store = store
        self.catalog = catalog
        self.work_root = Path(work_root)
        self.delay = delay

    def simulate(self, build):
        feature = self.catalog.by_id[build["feature_id"]]
        repo = self.work_root / build["build_id"]
        repo.mkdir(parents=True, exist_ok=True)
        diff = repo / "SIMULATED.diff"
        diff.write_text(f"Simulated patch for {feature['id']} {feature['title']}\n")
        digest = hashlib.sha256(diff.read_bytes()).hexdigest()
        return {
            "simulated": True,
            "feature_id": feature["id"],
            "artifact_digest": digest,
            "diff_summary": f"Simulated diff for {feature['id']} ({feature['title']})",
            "usage": {"simulated": True},
            "repo": str(repo),
        }

    def run_once(self):
        """Claim and finish at most one build. Returns None when nothing is dispatchable."""
        build = self.store.claim_next(self.catalog)
        if build is None:
            return None
        receipt = self.simulate(build)
        # A brief, bounded simulated delay keeps the live view observable.
        if self.delay:
            time.sleep(self.delay)
        result = self.store.complete_attempt(build["attempt_id"], build["attempt_generation"], receipt)
        return {"build_id": build["build_id"], "result": result}
