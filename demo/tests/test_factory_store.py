import json
import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.store import (
    Store, QUEUED, HELD, DISPATCHED, SIMULATED_COMPLETE, CANCELLED, MERGED, StoreError,
)


def feat(fid, depends_on=(), parallel=False, write=None, phase="P0"):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "fixture", "size": "S",
        "parallel": parallel, "phase": phase, "tier": 3,
        "write_paths": write or ["demo/forum/product/"],
        "depends_on": list(depends_on), "file": f"{fid}.md",
    }


def roots(n):
    return [feat(f"g{i:02d}") for i in range(1, n + 1)]


def fixture_catalog():
    features = [
        feat("f1"),
        feat("f2", depends_on=["f1"]),
        feat("f3", depends_on=["f2"]),
        feat("p1", parallel=True, write=["demo/forum/product/a/"]),
        feat("p2", parallel=True, write=["demo/forum/product/b/"]),
        feat("p3", parallel=True, write=["demo/forum/product/a/nested/"]),
    ]
    return Catalog({"schema_version": 2, "count": len(features), "features": features})


class StoreTests(unittest.TestCase):
    def test_dependency_hold_wakes_automatically_when_its_original_contract_is_satisfied(self):
        store=self.store()
        admitted=store.admit(['f2'],'wait',self.catalog)
        self.assertIsNone(store.claim_next(self.catalog))
        store.seed_merged('f1',self.catalog)
        claimed=store.claim_next(self.catalog)
        self.assertEqual(claimed['build_id'],admitted['build_ids'][0])
        self.assertEqual(claimed['status'],DISPATCHED)

    def test_changed_catalog_cannot_silently_dispatch_a_previously_queued_spec(self):
        store=self.store();store.admit(['f1'],'before-catalog-change',self.catalog)
        changed=fixture_catalog();changed.by_id['f1']['write_paths']=['demo/forum/product/changed/']
        self.assertIsNone(store.claim_next(changed))
        self.assertEqual(store.board()[0]['hold_reason'],'catalog_changed')
        self.assertIsNone(store.board()[0]['attempt_id'])

    def test_changed_catalog_or_uncertain_attempt_never_gets_automatic_dependency_retry(self):
        store=self.store();store.admit(['f2'],'wait',self.catalog)
        store.seed_merged('f1',self.catalog)
        changed=fixture_catalog();changed.by_id['f2']['write_paths']=['demo/forum/product/changed/']
        self.assertIsNone(store.claim_next(changed))
        self.assertEqual(store.board()[0]['hold_reason'],'catalog_changed')
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = fixture_catalog()

    def store(self, concurrency=1):
        return Store(Path(self.tmp.name) / "factory.db", active_concurrency=concurrency)

    def test_admit_root_is_queued(self):
        s = self.store()
        r = s.admit(["f1"], "k1", self.catalog)
        self.assertEqual(r["status"], "admitted")
        board = s.board()
        self.assertEqual(len(board), 1)
        self.assertEqual(board[0]["feature_id"], "f1")
        self.assertEqual(board[0]["status"], QUEUED)

    def test_admit_missing_dependency_holds(self):
        s = self.store()
        s.admit(["f2"], "k2", self.catalog)
        b = s.board()[0]
        self.assertEqual(b["status"], HELD)
        self.assertEqual(b["hold_reason"], "dependency_missing")

    def test_seeded_merged_dependency_allows_queue(self):
        s = self.store()
        s.seed_merged("f1", self.catalog)
        s.admit(["f2"], "k3", self.catalog)
        b = [x for x in s.board() if x["feature_id"] == "f2"][0]
        self.assertEqual(b["status"], QUEUED)

    def test_ten_item_cap_including_held(self):
        cat = Catalog({"schema_version": 2, "count": 11, "features": roots(11)})
        s = self.store()
        s.admit([f"g{i:02d}" for i in range(1, 11)], "k10", cat)
        self.assertEqual(s.nonterminal_count(), 10)
        r = s.admit(["g11"], "k11", cat)
        self.assertEqual(r["status"], "cap_exceeded")
        self.assertEqual(s.nonterminal_count(), 10)

    def test_idempotent_replay_and_conflict(self):
        s = self.store()
        first = s.admit(["f1"], "kdup", self.catalog)
        replay = s.admit(["f1"], "kdup", self.catalog)
        self.assertEqual(replay["status"], "replayed")
        self.assertEqual(replay["build_ids"], first["build_ids"])
        conflict = s.admit(["f2"], "kdup", self.catalog)
        self.assertEqual(conflict["status"], "conflict")

    def test_claim_and_complete_to_simulated(self):
        s = self.store()
        s.admit(["f1"], "k5", self.catalog)
        claimed = s.claim_next(self.catalog)
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["status"], DISPATCHED)
        done = s.complete_attempt(claimed["attempt_id"], claimed["attempt_generation"], {"simulated": True})
        self.assertEqual(done["status"], "completed")
        self.assertEqual(s.board()[0]["status"], SIMULATED_COMPLETE)

    def test_exclusive_concurrency_one(self):
        s = self.store()
        s.admit(["f1", "p1"], "k6", self.catalog)
        first = s.claim_next(self.catalog)
        self.assertIsNotNone(first)
        self.assertIsNone(s.claim_next(self.catalog))

    def test_disjoint_parallel_claim_when_concurrency_two(self):
        s = self.store(concurrency=2)
        s.admit(["p1", "p2"], "k7", self.catalog)
        a = s.claim_next(self.catalog)
        b = s.claim_next(self.catalog)
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertNotEqual(a["build_id"], b["build_id"])

    def test_overlapping_scopes_run_serially(self):
        s = self.store(concurrency=2)
        s.admit(["p1", "p3"], "k8", self.catalog)
        a = s.claim_next(self.catalog)
        self.assertIsNotNone(a)
        self.assertIsNone(s.claim_next(self.catalog))

    def test_cancel_rejects_late_result(self):
        s = self.store()
        s.admit(["f1"], "k9", self.catalog)
        claimed = s.claim_next(self.catalog)
        s.cancel(claimed["build_id"])
        done = s.complete_attempt(claimed["attempt_id"], claimed["attempt_generation"], {"simulated": True})
        self.assertEqual(done["status"], "stale_attempt")
        self.assertEqual(s.board()[0]["status"], CANCELLED)

    def test_cancel_terminal_is_refused(self):
        s = self.store()
        s.admit(["f1"], "k12", self.catalog)
        claimed = s.claim_next(self.catalog)
        s.complete_attempt(claimed["attempt_id"], claimed["attempt_generation"], {})
        self.assertEqual(s.cancel(claimed["build_id"])["status"], "already_terminal")

    def test_restart_reconciles_expired_lease_without_duplicate(self):
        path = Path(self.tmp.name) / "factory.db"
        s = Store(path)
        s.admit(["f1"], "k13", self.catalog)
        claimed = s.claim_next(self.catalog, lease_ns=0)
        # An interrupted paid call is uncertain, so recovery requires explicit review.
        s2 = Store(path)
        b = s2.board()[0]
        self.assertEqual(b["status"], HELD)
        self.assertEqual(b["hold_reason"], "reconciliation_needed")
        self.assertEqual(b["attempt_id"], claimed["attempt_id"])
        again = s2.claim_next(self.catalog)
        self.assertIsNone(again)

    def test_unknown_attempt_is_refused(self):
        s = self.store()
        self.assertEqual(s.complete_attempt("nope", 0, {})["status"], "unknown_attempt")


if __name__ == "__main__":
    unittest.main()
