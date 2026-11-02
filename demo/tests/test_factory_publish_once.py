"""The paid publish worker always holds its own forum purse and a positive reservation."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.publish_once import build_worker, positive_reservation
from factory.store import Store


class PublishWorkerBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.catalog = Catalog({"schema_version": 2, "count": 1,
                                "features": [{"id": "001", "title": "One", "area": "foundation",
                                              "size": "S", "parallel": False, "phase": "P0",
                                              "tier": 3, "write_paths": ["src/"],
                                              "depends_on": [], "file": "001.md"}]})

    def test_positive_reservation_refuses_zero_and_invalid_amounts(self):
        self.assertEqual(positive_reservation("0.10"), "0.10")
        for value in ("0", "0.001", "-0.01", "not-a-number"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    positive_reservation(value)

    def test_the_worker_is_wired_to_the_forum_purse(self):
        ledger = self.root / "shared" / "ledger.jsonl"
        worker = build_worker(Store(self.root / "factory.db"), self.catalog,
                              self.root / "specs", self.root, "o/r", "model",
                              lambda model, prompt: {"verdict": "approve"}, "0.10", ledger)
        self.assertEqual(worker.budget_scope, "aeion-autonomous-forum")
        self.assertIsNotNone(worker.budget)
        self.assertEqual(worker.budget.path, ledger)
        self.assertEqual(worker.config["cost_reservation_usd"], "0.10")
        self.assertFalse(worker.allow_unbudgeted)


if __name__ == "__main__":
    unittest.main()
