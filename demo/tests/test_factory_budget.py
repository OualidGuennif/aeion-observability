"""The two daily purses: journal first, settle after, fail closed past $15."""
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.budget import BudgetError, DailyBudget

DAY = "2026-11-02"


def budget(root, limits=None):
    return DailyBudget(root / "ledger.jsonl", limits=limits, today=lambda: DAY)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_reserve_then_settle_journals_the_actual_cost(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.10", note="run-1")
        self.assertEqual(b.spent("aeion-observability"), Decimal("0.10"))
        self.assertEqual(b.settle(reservation, "0.10"), Decimal("0.10"))
        self.assertEqual(b.spent("aeion-observability"), Decimal("0.10"))
        self.assertEqual(b.remaining("aeion-observability"), Decimal("14.90"))
        lines = (self.root / "ledger.jsonl").read_text().splitlines()
        self.assertEqual([json.loads(line)["kind"] for line in lines], ["reserve", "settle"])

    def test_an_open_reservation_counts_against_the_day(self):
        b = budget(self.root)
        b.admit("aeion-observability", "14.50")
        with self.assertRaisesRegex(BudgetError, "budget_unavailable"):
            b.admit("aeion-observability", "0.60")

    def test_a_scope_cannot_spend_past_its_limit(self):
        b = budget(self.root)
        b.admit("aeion-observability", "14.95")
        with self.assertRaisesRegex(BudgetError, "budget_unavailable"):
            b.admit("aeion-observability", "0.10")
        self.assertEqual(b.spent("aeion-observability"), Decimal("14.95"))

    def test_a_higher_actual_cost_counts_and_the_next_call_is_refused(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.10")
        self.assertEqual(b.settle(reservation, "1.00"), Decimal("1.00"))
        with self.assertRaises(BudgetError):
            b.admit("aeion-observability", "14.50")

    def test_settling_twice_is_idempotent(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.10")
        b.settle(reservation, "0.10")
        self.assertEqual(b.settle(reservation, "9.99"), Decimal("0.10"))

    def test_the_two_purses_are_independent(self):
        b = budget(self.root)
        b.admit("aeion-observability", "15.00")
        self.assertEqual(b.remaining("aeion-observability"), Decimal("0"))
        self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("15.00"))
        b.admit("aeion-autonomous-forum", "15.00")

    def test_zero_cost_is_still_journalled(self):
        b = budget(self.root)
        reservation = b.admit("aeion-autonomous-forum", "0.00", note="fake-build")
        self.assertEqual(b.settle(reservation, "0.00"), Decimal("0"))
        record = json.loads((self.root / "ledger.jsonl").read_text().splitlines()[0])
        self.assertEqual(record["usd"], "0.00")

    def test_an_unknown_scope_is_refused(self):
        with self.assertRaisesRegex(BudgetError, "budget_unknown_scope"):
            budget(self.root).admit("someone-else", "0.01")

    def test_an_unknown_reservation_is_refused(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.10")
        other = type(reservation)(id="0" * 32, scope=reservation.scope,
                                  day=reservation.day, estimate_usd=reservation.estimate_usd)
        with self.assertRaisesRegex(BudgetError, "unknown_reservation"):
            b.settle(other, "0.10")

    def test_a_corrupt_ledger_fails_closed(self):
        (self.root / "ledger.jsonl").write_text("not json\n")
        with self.assertRaisesRegex(BudgetError, "budget_ledger_corrupt"):
            budget(self.root).spent("aeion-observability")

    def test_summary_reports_both_purses(self):
        b = budget(self.root)
        b.admit("aeion-observability", "0.25")
        summary = b.summary()
        self.assertEqual(summary["aeion-observability"]["limit_usd"], "15.00")
        self.assertEqual(summary["aeion-observability"]["spent_usd"], "0.25")
        self.assertEqual(summary["aeion-autonomous-forum"]["spent_usd"], "0.00")


if __name__ == "__main__":
    unittest.main()
