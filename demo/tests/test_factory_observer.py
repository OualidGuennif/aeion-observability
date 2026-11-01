import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.observer import Observer
from factory.store import SIMULATED_COMPLETE, Store, QUEUED


def feat(fid):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum/product/"], "depends_on": [], "file": f"{fid}.md",
    }


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cat = Catalog({"schema_version": 2, "count": 2,
                            "features": [feat("001"), feat("002")]})
        self.store = Store(Path(self.tmp.name) / "factory.db")
        self.observer = Observer(self.store)

    def _complete(self, fid):
        self.store.admit([fid], f"k-{fid}", self.cat)
        build_id = self.store.board()[-1]["build_id"]
        self.store.claim_next(self.cat)
        self.store.complete_attempt(
            self.store.board()[-1]["attempt_id"], 0,
            {"simulated": True, "artifact_digest": f"dig-{fid}"},
            terminal=SIMULATED_COMPLETE,
        )
        return build_id

    def test_proposes_completed_build_once(self):
        build_id = self._complete("001")
        proposals = self.observer.propose()
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["build_id"], build_id)
        self.assertEqual(proposals[0]["artifact_digest"], "dig-001")
        # Bounded metadata: no receipt body leaked.
        self.assertNotIn("receipt", proposals[0])
        # Deduplicated: a second pass proposes nothing.
        self.assertEqual(self.observer.propose(), [])

    def test_dedup_survives_new_observer_instance(self):
        self._complete("001")
        first = Observer(self.store).propose()
        self.assertEqual(len(first), 1)
        second = Observer(self.store).propose()
        self.assertEqual(second, [])

    def test_ignores_non_completed_builds(self):
        self.store.admit(["001"], "k-q", self.cat)
        self.assertEqual(self.store.board()[0]["status"], QUEUED)
        self.assertEqual(self.observer.propose(), [])

    def test_max_batch_bounds_the_batch(self):
        self._complete("001")
        self._complete("002")
        bounded = Observer(self.store, max_batch=1).propose()
        self.assertEqual(len(bounded), 1)

    def test_proposal_marker_is_persisted(self):
        build_id = self._complete("001")
        self.observer.propose()
        stored = self.store.meta_get(f"observer:proposed:{build_id}")
        self.assertIsNotNone(stored)
        self.assertEqual(json.loads(stored)["build_id"], build_id)


if __name__ == "__main__":
    unittest.main()
