import json
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import Store, QUEUED, SIMULATED_COMPLETE, CANCELLED
from factory.worker import FakeWorker
from factory.sse import SseHub


def feat(fid, depends_on=()):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "fixture", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum/product/"], "depends_on": list(depends_on), "file": f"{fid}.md",
    }


def catalog(*ids):
    return Catalog({"schema_version": 2, "count": len(ids), "features": [feat(i) for i in ids]})


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / "factory.db")
        self.cat = catalog("f1", "f2")

    def worker(self):
        return FakeWorker(self.store, self.cat, Path(self.tmp.name) / "work", delay=0)

    def test_run_once_idle_when_nothing_queued(self):
        self.assertIsNone(self.worker().run_once())

    def test_run_once_completes_simulated(self):
        self.store.admit(["f1"], "k1", self.cat)
        result = self.worker().run_once()
        self.assertEqual(result["result"]["status"], "completed")
        build = self.store.board()[0]
        self.assertEqual(build["status"], SIMULATED_COMPLETE)
        receipt = json.loads(build["receipt"])
        self.assertTrue(receipt["simulated"])
        self.assertIn("artifact_digest", receipt)

    def test_cancel_during_work_leaves_cancelled(self):
        self.store.admit(["f1"], "k2", self.cat)
        claimed = self.store.claim_next(self.cat)
        self.store.cancel(claimed["build_id"])
        # The late fake result cannot advance a cancelled build.
        done = self.store.complete_attempt(claimed["attempt_id"], claimed["attempt_generation"], {"simulated": True})
        self.assertEqual(done["status"], "stale_attempt")
        self.assertEqual(self.store.board()[0]["status"], CANCELLED)


class SseHubTests(unittest.TestCase):
    def test_publish_and_replay_from_cursor(self):
        hub = SseHub()
        hub.publish("queued", {"id": "a"})
        hub.publish("dispatched", {"id": "a"})
        self.assertEqual(len(hub.replay(0)), 2)
        self.assertEqual(len(hub.replay(1)), 1)

    def test_bounded_buffer_advances_earliest(self):
        hub = SseHub(max_events=3)
        for i in range(5):
            hub.publish("e", i)
        self.assertEqual(hub.earliest_seq(), 3)
        self.assertEqual([f["seq"] for f in hub.replay(0)], [3, 4, 5])


if __name__ == "__main__":
    unittest.main()
