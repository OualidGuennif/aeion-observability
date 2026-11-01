#!/usr/bin/env python3
"""Fixture tests for tools/knowledge/knowledge-check: a throwaway root, the real tool run with --root.

Run with: python3 tools/knowledge/tests/test_knowledge_check.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "knowledge-check"
FIELDS = "- Owner decision: x\n- State: x\n- Next: x (who: agent)\n- Blocker: none\n- Evidence: x\n"
failures, passes = [], 0


def check(name, current, want_code, want_text=""):
    global passes
    root = Path(tempfile.mkdtemp())
    (root / "work").mkdir()
    (root / "work/current.md").write_text("# Current work\n\n" + current)
    r = subprocess.run([sys.executable, str(TOOL), "--root", str(root)], capture_output=True, text=True)
    if r.returncode == want_code and want_text in r.stdout:
        passes += 1
    else:
        failures.append(f"{name}: exit {r.returncode}, stdout {r.stdout!r}")


check("a complete entry passes", "## A task — ACTIVE\n" + FIELDS, 0, "PASS")
# A missing field names itself and the whole shape, so the next entry is written right (Pi FB-001).
check("a missing field is named", "## A task — ACTIVE\n- State: x\n", 1, "lacks '- Owner decision:'")
check("a missing field prints the shape", "## A task — ACTIVE\n- State: x\n", 1,
      "an entry is '## <title> — <STATUS>' then the lines - Owner decision: / - State: / - Next: / - Blocker: / - Evidence:")
check("an entry over 10 lines", "## A task — ACTIVE\n" + FIELDS + "- more\n" * 6, 1, "over 10 lines")


def check_doc(name, extra, want_code, want_text=""):
    global passes
    root = Path(tempfile.mkdtemp())
    (root / "knowledge/policies").mkdir(parents=True)
    (root / "knowledge/policies/volatile.md").write_text(
        "---\ntype: Reference\ntitle: \"Volatile\"\ndescription: \"Volatile.\"\nstatus: draft\n"
        + extra + "---\n\nBody.\n")
    r = subprocess.run([sys.executable, str(TOOL), "--root", str(root)], capture_output=True, text=True)
    if r.returncode == want_code and want_text in r.stdout:
        passes += 1
    else:
        failures.append(f"{name}: exit {r.returncode}, stdout {r.stdout!r}")


check_doc("a review_after date is accepted", "review_after: 2027-01-29\n", 0, "PASS")
check_doc("a missing review_after is not a problem", "", 0, "PASS")
for value in ('', '""', '"  "'):
    check_doc("an explicitly empty review_after is invalid", f"review_after: {value}\n", 1,
              "is not a YYYY-MM-DD date")
check_doc("a malformed review_after is named", "review_after: 2027-1-9\n", 1,
          "review_after '2027-1-9' is not a YYYY-MM-DD date")

for f in failures:
    print("FAIL:", f)
print(f"{passes} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
