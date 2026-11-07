"""The two daily purses: journal first, settle after, fail closed past the daily cap."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import budget as budget_module
from factory.budget import BudgetError, DailyBudget, paris_day

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
        self.assertEqual(b.remaining("aeion-observability"), Decimal("149.90"))
        lines = (self.root / "ledger.jsonl").read_text().splitlines()
        self.assertEqual([json.loads(line)["kind"] for line in lines], ["reserve", "settle"])

    def test_an_open_reservation_counts_against_the_day(self):
        b = budget(self.root)
        b.admit("aeion-observability", "149.50")
        with self.assertRaisesRegex(BudgetError, "budget_unavailable"):
            b.admit("aeion-observability", "0.60")

    def test_a_scope_cannot_spend_past_its_limit(self):
        b = budget(self.root)
        b.admit("aeion-observability", "149.95")
        with self.assertRaisesRegex(BudgetError, "budget_unavailable"):
            b.admit("aeion-observability", "0.10")
        self.assertEqual(b.spent("aeion-observability"), Decimal("149.95"))

    def test_a_higher_actual_cost_counts_and_the_next_call_is_refused(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.10")
        self.assertEqual(b.settle(reservation, "1.00"), Decimal("1.00"))
        with self.assertRaises(BudgetError):
            b.admit("aeion-observability", "149.50")

    def test_settling_twice_is_idempotent(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.10")
        b.settle(reservation, "0.10")
        self.assertEqual(b.settle(reservation, "9.99"), Decimal("0.10"))

    def test_the_two_purses_are_independent(self):
        b = budget(self.root)
        b.admit("aeion-observability", "150.00")
        self.assertEqual(b.remaining("aeion-observability"), Decimal("0"))
        self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("150.00"))
        b.admit("aeion-autonomous-forum", "150.00")

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

    def test_a_line_missing_its_day_or_reservation_fails_closed(self):
        for line in (
            {"version": 1, "kind": "reserve", "scope": "aeion-observability",
             "reservation": "a" * 32, "usd": "0.00"},
            {"version": 1, "kind": "reserve", "scope": "aeion-observability",
             "day": DAY, "usd": "0.00"},
        ):
            with self.subTest(line=line):
                (self.root / "ledger.jsonl").write_text(json.dumps(line) + "\n")
                with self.assertRaisesRegex(BudgetError, "budget_ledger_corrupt"):
                    budget(self.root).spent("aeion-observability")

    def test_a_positive_sub_cent_reservation_is_rounded_up_not_free(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.001")
        self.assertEqual(reservation.estimate_usd, Decimal("0.01"))
        self.assertEqual(b.spent("aeion-observability"), Decimal("0.01"))
        self.assertEqual(b.settle(reservation, "0.001"), Decimal("0.01"))

    def test_a_zero_reservation_cannot_settle_a_positive_cost(self):
        b = budget(self.root)
        reservation = b.admit("aeion-observability", "0.00")
        with self.assertRaisesRegex(BudgetError, "settlement_exceeds_reservation"):
            b.settle(reservation, "0.01")
        self.assertEqual(b.spent("aeion-observability"), Decimal("0.00"))

    def test_summary_reports_both_purses(self):
        b = budget(self.root)
        b.admit("aeion-observability", "0.25")
        summary = b.summary()
        self.assertEqual(summary["aeion-observability"]["limit_usd"], "150.00")
        self.assertEqual(summary["aeion-observability"]["spent_usd"], "0.25")
        self.assertEqual(summary["aeion-observability"]["settled_usd"], "0.00")
        self.assertEqual(summary["aeion-observability"]["reserved_usd"], "0.25")
        self.assertEqual(summary["aeion-autonomous-forum"]["spent_usd"], "0.00")
        self.assertEqual(summary["aeion-autonomous-forum"]["settled_usd"], "0.00")
        self.assertEqual(summary["aeion-autonomous-forum"]["reserved_usd"], "0.00")
        reservation = b.admit("aeion-autonomous-forum", "1.00")
        b.settle(reservation, "0.40")
        split = b.summary()
        self.assertEqual(split["aeion-autonomous-forum"]["settled_usd"], "0.40")
        self.assertEqual(split["aeion-autonomous-forum"]["reserved_usd"], "0.00")
        self.assertEqual(split["aeion-autonomous-forum"]["spent_usd"], "0.40")


class BudgetDayTests(unittest.TestCase):
    def test_the_budget_day_is_europe_paris_across_midnight(self):
        self.assertEqual(
            paris_day(datetime(2026, 11, 2, 23, 30, tzinfo=timezone.utc)), "2026-11-03")
        self.assertEqual(
            paris_day(datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)), "2026-11-02")

    def test_a_default_budget_uses_the_paris_day(self):
        fixed = datetime(2026, 11, 2, 23, 30, tzinfo=timezone.utc)
        with mock.patch.object(budget_module, "datetime") as clock:
            clock.now.return_value = fixed
            with tempfile.TemporaryDirectory() as root:
                b = DailyBudget(Path(root) / "ledger.jsonl")
                b.admit("aeion-observability", "0.10")
                self.assertEqual(b.summary()["aeion-observability"]["day"], "2026-11-03")


class BudgetSettingsTests(unittest.TestCase):
    """budget.conf may lower the owner ceilings, never raise them; invalid means no spending."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.conf = Path(self.tmp.name) / "budget.conf"
        patcher = mock.patch.dict("os.environ", {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in (*budget_module.CEILINGS, *budget_module.TIME_LIMITS):
            budget_module.os.environ.pop("AEION_" + key, None)

    def settings(self, text):
        self.conf.write_text(text)
        return budget_module.settings(self.conf)

    def test_the_shipped_file_is_valid_and_within_the_owner_ceilings(self):
        bounds = budget_module.settings()
        self.assertEqual(bounds["DAILY_LIMIT_USD"], Decimal("150.00"))
        self.assertEqual(bounds["AUTHOR_MAX_USD"], Decimal("50.00"))
        self.assertEqual(bounds["REVIEW_MAX_USD"], Decimal("1.00"))

    def test_owner_values_up_to_each_ceiling_are_accepted(self):
        bounds = self.settings("DAILY_LIMIT_USD=150.00\nAUTHOR_MAX_USD=50.00  # extreme case\nREVIEW_MAX_USD=0.50\n")
        self.assertEqual(bounds["AUTHOR_MAX_USD"], Decimal("50.00"))
        self.assertEqual(bounds["REVIEW_MAX_USD"], Decimal("0.50"))

    def test_values_above_a_ceiling_unknown_keys_or_nonsense_are_refused_whole(self):
        for text in ("AUTHOR_MAX_USD=50.01\n", "DAILY_LIMIT_USD=151\n", "REVIEW_MAX_USD=2\n",
                     "AUTHOR_MAX_USD=0\n", "AUTHOR_MAX_USD=-1\n", "AUTHOR_MAX_USD=NaN\n",
                     "AUTHOR_MAX_USD=Infinity\n", "AUTHOR_MAX_USD=abc\n", "TASK_MAX=3\n", "AUTHOR_MAX_USD\n",
                     "DAILY_LIMIT_USD=2.00\nAUTHOR_MAX_USD=1.00\nREVIEW_MAX_USD=0.60\n"):
            with self.subTest(text=text), self.assertRaisesRegex(BudgetError, "budget_config_invalid"):
                self.settings(text)

    def test_the_author_window_is_whole_minutes_between_five_and_one_eighty(self):
        self.conf.write_text("")
        self.assertEqual(budget_module.author_timeout_seconds(self.conf), 1800)
        self.conf.write_text("AUTHOR_TIMEOUT_MINUTES=180\n")
        self.assertEqual(budget_module.author_timeout_seconds(self.conf), 10800)
        self.assertEqual(budget_module.settings(self.conf)["AUTHOR_MAX_USD"], Decimal("50.00"))
        for raw in ("181", "4", "0", "-30", "90.5", "abc", "1e2", "\u0661\u0662\u0660", ""):
            with self.subTest(raw=raw):
                self.conf.write_text(f"AUTHOR_TIMEOUT_MINUTES={raw}\n")
                with self.assertRaisesRegex(BudgetError, "budget_config_invalid"):
                    budget_module.author_timeout_seconds(self.conf)
                with self.assertRaisesRegex(BudgetError, "budget_config_invalid"):
                    budget_module.settings(self.conf)
        budget_module.os.environ["AEION_AUTHOR_TIMEOUT_MINUTES"] = "60"
        self.conf.write_text("AUTHOR_TIMEOUT_MINUTES=180\n")
        self.assertEqual(budget_module.author_timeout_seconds(self.conf), 3600)
        budget_module.os.environ["AEION_AUTHOR_TIMEOUT_MINUTES"] = "600"
        with self.assertRaisesRegex(BudgetError, "budget_config_invalid"):
            budget_module.author_timeout_seconds(self.conf)

    def test_the_shipped_author_window_is_within_the_ceiling(self):
        from factory.freeze import AUTHOR_TIMEOUT_CEILING_SECONDS
        self.assertLessEqual(budget_module.author_timeout_seconds(), AUTHOR_TIMEOUT_CEILING_SECONDS)
        self.assertEqual(budget_module.TIME_LIMITS["AUTHOR_TIMEOUT_MINUTES"][1] * 60, AUTHOR_TIMEOUT_CEILING_SECONDS)

    def test_an_exported_override_wins_but_cannot_pass_a_ceiling(self):
        budget_module.os.environ["AEION_AUTHOR_MAX_USD"] = "3.00"
        self.assertEqual(self.settings("AUTHOR_MAX_USD=1.00\n")["AUTHOR_MAX_USD"], Decimal("3.00"))
        budget_module.os.environ["AEION_AUTHOR_MAX_USD"] = "50"
        self.assertEqual(self.settings("AUTHOR_MAX_USD=1.00\n")["AUTHOR_MAX_USD"], Decimal("50.00"))
        budget_module.os.environ["AEION_AUTHOR_MAX_USD"] = "50.01"
        with self.assertRaisesRegex(BudgetError, "budget_config_invalid"):
            self.settings("AUTHOR_MAX_USD=1.00\n")

    def test_an_invalid_file_leaves_a_zero_purse_that_admits_nothing(self):
        self.conf.write_text("DAILY_LIMIT_USD=999\n")
        with mock.patch.object(budget_module, "CONFIG_PATH", self.conf):
            b = DailyBudget(Path(self.tmp.name) / "ledger.jsonl", today=lambda: DAY)
            self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("0"))
            with self.assertRaisesRegex(BudgetError, "budget_unavailable"):
                b.admit("aeion-autonomous-forum", "0.01")

    def test_the_daily_purse_follows_the_file(self):
        self.conf.write_text("DAILY_LIMIT_USD=6.00\nAUTHOR_MAX_USD=2.00\nREVIEW_MAX_USD=1.00\n")
        with mock.patch.object(budget_module, "CONFIG_PATH", self.conf):
            b = DailyBudget(Path(self.tmp.name) / "ledger.jsonl", today=lambda: DAY)
            self.assertEqual(b.remaining("aeion-autonomous-forum"), Decimal("6.00"))


if __name__ == "__main__":
    unittest.main()
