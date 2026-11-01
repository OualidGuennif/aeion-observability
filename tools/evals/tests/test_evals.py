#!/usr/bin/env python3
"""Fixture tests for tools/evals/record and tools/evals/report, run through subprocess.

Run with: python3 tools/evals/tests/test_evals.py
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

EVALS = Path(__file__).resolve().parents[1]
RECORD = EVALS / "record"
REPORT = EVALS / "report"


class EvalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.file = self.folder / "nested" / "results.jsonl"

    def run_tool(self, tool, *args):
        return subprocess.run([sys.executable, str(tool), *args], capture_output=True, text=True)

    def record(self, *args):
        return self.run_tool(RECORD, "--task", "golden", "--harness", "claude-code",
                             "--success", "yes", "--minutes", "10", "--file", str(self.file), *args)

    def lines(self):
        return self.file.read_text(encoding="utf-8").splitlines()

    def report_rows(self, rows, *args):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return self.run_tool(REPORT, "--file", str(self.file), *args)

    def valid_row(self, **fields):
        return dict(task="a", harness="pi", success=True, minutes=1,
                    factory="1.8.0", recorded_at="2026-10-31T00:00:00Z", **fields)

    def test_valid_record_appends_one_parseable_line(self):
        result = self.record("--model", "m", "--tokens", "100", "--cost-usd", "0.5",
                             "--human-interventions", "2", "--notes", "n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith(str(self.file) + ": golden"))
        self.assertEqual(len(self.lines()), 1)
        row = json.loads(self.lines()[0])
        self.assertEqual((row["task"], row["harness"], row["success"], row["minutes"]), ("golden", "claude-code", True, 10.0))
        self.assertEqual((row["tokens"], row["cost_usd"], row["human_interventions"]), (100, 0.5, 2))
        self.assertTrue(row["recorded_at"].endswith("Z"))
        self.assertTrue(row["factory"])

    def test_invalid_task_slug_exits_two_and_writes_nothing(self):
        result = self.run_tool(RECORD, "--task", "Bad_Task", "--harness", "claude-code",
                               "--success", "yes", "--minutes", "1", "--file", str(self.file))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--task", result.stderr)
        self.assertFalse(self.file.exists())

    def test_missing_required_flag_exits_two(self):
        result = self.run_tool(RECORD, "--task", "golden", "--harness", "claude-code",
                               "--success", "yes", "--file", str(self.file))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--minutes", result.stderr)
        self.assertFalse(self.file.exists())

    def test_two_records_make_two_lines(self):
        self.assertEqual(self.record().returncode, 0)
        self.assertEqual(self.record("--success", "no").returncode, 0)
        self.assertEqual(len(self.lines()), 2)
        self.assertEqual([json.loads(line)["success"] for line in self.lines()], [True, False])

    def test_append_preserves_a_record_without_a_final_newline(self):
        self.assertEqual(self.record("--notes", "first évaluation").returncode, 0)
        before = self.file.read_bytes().rstrip(b"\n")
        self.file.write_bytes(before)
        self.assertEqual(self.record("--success", "no").returncode, 0)
        self.assertTrue(self.file.read_bytes().startswith(before + b"\n"))
        self.assertEqual([json.loads(line)["success"] for line in self.lines()], [True, False])
        result = self.run_tool(REPORT, "--file", str(self.file), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["all"]["runs"], 2)

    def test_dry_run_prints_json_and_writes_nothing(self):
        result = self.record("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["task"], "golden")
        self.assertFalse(self.file.exists())
        self.assertFalse(self.file.parent.exists())

    def assert_non_finite_refused(self, flag, value):
        result = self.record(flag, value)
        self.assertEqual(result.returncode, 2)
        self.assertIn(flag, result.stderr)
        self.assertFalse(self.file.exists())

    def test_nan_minutes_exits_two_and_writes_nothing(self):
        self.assert_non_finite_refused("--minutes", "nan")

    def test_infinite_minutes_exits_two_and_writes_nothing(self):
        self.assert_non_finite_refused("--minutes", "inf")

    def test_nan_cost_exits_two_and_writes_nothing(self):
        self.assert_non_finite_refused("--cost-usd", "nan")

    def test_infinite_cost_exits_two_and_writes_nothing(self):
        self.assert_non_finite_refused("--cost-usd", "inf")

    def test_non_finite_cost_leaves_an_existing_file_unchanged(self):
        self.assertEqual(self.record().returncode, 0)
        before = self.file.read_text(encoding="utf-8")
        result = self.record("--cost-usd", "nan")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--cost-usd", result.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), before)

    def test_report_over_three_fixtures(self):
        rows = [
            {"task": "a", "harness": "claude-code", "success": True, "minutes": 10, "cost_usd": 1.5,
             "human_interventions": 1, "defects_after_done": 0, "factory": "1.7.0", "recorded_at": "2026-10-31T00:00:00Z"},
            {"task": "b", "harness": "claude-code", "success": False, "minutes": 20, "cost_usd": 2.5,
             "human_interventions": 2, "defects_after_done": 1, "factory": "1.7.0", "recorded_at": "2026-10-31T00:00:00Z"},
            {"task": "a", "harness": "pi", "success": True, "minutes": 5, "factory": "1.7.0",
             "recorded_at": "2026-10-31T00:00:00Z"},
        ]
        self.file.parent.mkdir(parents=True)
        self.file.write_text("\n".join(json.dumps(row) for row in rows) + "\n\n", encoding="utf-8")
        result = self.run_tool(REPORT, "--file", str(self.file))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("claude-code", result.stdout)
        self.assertIn("pi", result.stdout)
        self.assertIn("| All |", result.stdout)
        self.assertIn("| 15.0 |", result.stdout)  # median of 5, 10, 20
        self.assertIn("| 67% |", result.stdout)  # 2 successes of 3
        self.assertIn("| N/A | N/A | N/A |", result.stdout)
        as_json = self.run_tool(REPORT, "--file", str(self.file), "--json")
        self.assertEqual(as_json.returncode, 0, as_json.stderr)
        report = json.loads(as_json.stdout)
        self.assertEqual([row["harness"] for row in report["harnesses"]], ["claude-code", "pi"])
        self.assertEqual(report["all"]["runs"], 3)
        self.assertEqual(report["all"]["median_minutes"], 10.0)
        self.assertEqual(report["harnesses"][0]["cost_usd"], 4.0)
        self.assertIsNone(report["all"]["cost_usd"])
        self.assertIsNone(report["all"]["human_interventions"])

    def test_missing_optional_metrics_stay_unknown(self):
        result = self.report_rows([self.valid_row()], "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)["all"]
        for key in ("cost_usd", "human_interventions", "defects_after_done"):
            self.assertIsNone(row[key], key)
        table = self.run_tool(REPORT, "--file", str(self.file))
        self.assertEqual(table.returncode, 0, table.stderr)
        self.assertIn("| N/A | N/A | N/A |", table.stdout)

    def test_explicit_zero_and_complete_totals_remain_numeric(self):
        rows = [self.valid_row(cost_usd=0, human_interventions=0, defects_after_done=0),
                self.valid_row(cost_usd=1.5, human_interventions=2, defects_after_done=1)]
        result = self.report_rows(rows, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        row = json.loads(result.stdout)["all"]
        self.assertEqual((row["cost_usd"], row["human_interventions"], row["defects_after_done"]), (1.5, 2, 1))
        zero = self.report_rows(rows[:1], "--json")
        self.assertEqual(json.loads(zero.stdout)["all"]["cost_usd"], 0)

    def test_partial_metric_is_unknown_even_within_one_harness(self):
        result = self.report_rows([self.valid_row(cost_usd=2), self.valid_row()], "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIsNone(report["all"]["cost_usd"])
        self.assertIsNone(report["harnesses"][0]["cost_usd"])

    def test_each_missing_required_field_names_its_line_and_field(self):
        for key in ("task", "harness", "success", "minutes", "factory", "recorded_at"):
            with self.subTest(field=key):
                row = self.valid_row()
                del row[key]
                result = self.report_rows([self.valid_row(), row], "--json")
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(f"{self.file}:2:", result.stderr)
                self.assertIn(key, result.stderr)

    def test_invalid_record_types_and_numbers_are_refused(self):
        cases = [("task", "Bad_Task"), ("harness", ""), ("success", "yes"),
                 ("minutes", True), ("minutes", "1"), ("minutes", -1),
                 ("minutes", float("nan")), ("minutes", float("inf")),
                 ("cost_usd", None), ("cost_usd", -1), ("cost_usd", float("nan")),
                 ("tokens", 1.5), ("human_interventions", True),
                 ("rework_commits", -1), ("defects_after_done", "0"), ("notes", {})]
        for key, value in cases:
            with self.subTest(field=key, value=value):
                row = dict(self.valid_row(), **{key: value})
                result = self.report_rows([row], "--json")
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(f"{self.file}:1:", result.stderr)
                self.assertIn(key, result.stderr)

    def test_non_object_and_invalid_timestamps_are_refused(self):
        for row in [[], None, dict(self.valid_row(), recorded_at="not-a-date"),
                    dict(self.valid_row(), recorded_at="2026-10-31")]:
            with self.subTest(row=row):
                result = self.report_rows([row], "--json")
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(f"{self.file}:1:", result.stderr)

    def test_report_over_an_empty_file(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text("", encoding="utf-8")
        result = self.run_tool(REPORT, "--file", str(self.file))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No evaluation records.", result.stdout)

    def test_report_over_a_malformed_line_exits_two(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text(json.dumps(self.valid_row()) + '\nnot json\n', encoding="utf-8")
        result = self.run_tool(REPORT, "--file", str(self.file))
        self.assertEqual(result.returncode, 2)
        self.assertIn(":2:", result.stderr)


if __name__ == "__main__":
    unittest.main()
