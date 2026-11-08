"""The live status report prints names and supervisor CI lines, never reviewer prose."""
import json
import sqlite3
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.live_status import (
    ci_lines, feature_lines, format_progress, parse_procargs, protection_lines)

NOW = 1_000_000_000_000
REVIEWER = "A reviewer approved it, noting: change the default database flag"


def database():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE builds (build_id TEXT, feature_id TEXT, status TEXT, hold_reason TEXT, "
        "receipt TEXT, updated_ns INTEGER, lease_until_ns INTEGER)")
    conn.execute(
        "CREATE TABLE events (seq INTEGER PRIMARY KEY, build_id TEXT, time_ns INTEGER, "
        "event TEXT, detail TEXT)")
    previous = {
        "publisher": {"reason": "ci_failed", "failed_checks": [
            {"name": "Knowledge, links and repository health", "conclusion": "failure"}]},
        "correction": {"trigger": "ci_failed"},
        "circuit": {"votes": [{"verdict": "approve", "reason": "change the default database flag"}]},
    }
    current = {"progress": {"phase": "model.step.started", "detail": {}}}
    conn.execute("INSERT INTO builds VALUES (?,?,?,?,?,?,?)",
                 ("a" * 32, "001", "failed", "", json.dumps(previous), NOW - 5_000_000_000, 0))
    conn.execute("INSERT INTO builds VALUES (?,?,?,?,?,?,?)",
                 ("b" * 32, "001", "dispatched", "", json.dumps(current), NOW - 2_000_000_000, NOW + 1))
    conn.execute(
        "INSERT INTO events (build_id, time_ns, event, detail) VALUES (?,?,?,?)",
        ("b" * 32, NOW - 1_000_000_000, "correction",
         json.dumps({"previous_build_id": "a" * 32, "attempt": 1, "round": 2})))
    conn.execute(
        "INSERT INTO events (build_id, time_ns, event, detail) VALUES (?,?,?,?)",
        ("b" * 32, NOW - 1_000_000_000, "progress",
         json.dumps({"phase": "reviewing", "detail": {"status": "running"}})))
    return conn


class LiveStatusTests(unittest.TestCase):
    def test_procargs_reports_live_mode_without_returning_pairs(self):
        data = (2).to_bytes(4, "little") + b"/usr/bin/Python\0\0/usr/bin/Python\0demo/app/server.py\0"
        data += b"AEION_FACTORY_EXECUTION=live\0GH_API_KEY=secret-value\0"
        argc, args, mode_live = parse_procargs(data)
        self.assertEqual(argc, 2)
        self.assertEqual(args, ["/usr/bin/Python", "demo/app/server.py"])
        self.assertTrue(mode_live)
        self.assertNotIn("secret-value", " ".join(args))

    def test_ci_lines_keep_the_supervisor_sentence_only(self):
        kept, others = ci_lines([
            "Required CI failed: Knowledge, links and repository health (failure).",
            "Supervisor: Repair this check only: update the owning document.",
            REVIEWER])
        self.assertEqual(len(kept), 2)
        self.assertEqual(others, 1)
        self.assertNotIn(REVIEWER, "\n".join(kept))

    def test_protection_lines_name_the_checks_and_the_http_status(self):
        text = "\n".join(protection_lines({
            "status": "qualified", "checks": ["secret-scan", "not a check\n"]}))
        self.assertIn("http=200", text)
        self.assertIn("checks=secret-scan", text)
        self.assertNotIn("not a check", text)

    def test_a_feature_report_omits_reviewer_prose(self):
        conn = database()
        text = "\n".join(feature_lines(conn, "001", NOW, feedback=True))
        self.assertIn("status=dispatched", text)
        self.assertIn("progress=reviewing", text)
        self.assertIn("correction_round=2", text)
        self.assertIn("check=Knowledge, links and repository health (failure)", text)
        self.assertIn("Required CI failed: Knowledge, links and repository health (failure).", text)
        self.assertIn("other_feedback_lines=1", text)
        self.assertNotIn("default database flag", text)
        self.assertNotIn(REVIEWER, text)

    def test_a_progress_event_keeps_only_status_names(self):
        raw = json.dumps({"phase": "model.step.started", "detail": {
            "status": "running", "reason": "not a token", "step": 3}})
        line = format_progress(raw, NOW, NOW - 4_000_000_000)
        self.assertIn("progress=model.step.started", line)
        self.assertIn("reason=-", line)
        self.assertIn("step=3", line)
        self.assertIn("age_s=4", line)


if __name__ == "__main__":
    unittest.main()
