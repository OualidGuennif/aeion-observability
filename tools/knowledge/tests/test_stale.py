#!/usr/bin/env python3
"""Fixture tests for tools/knowledge/stale: a throwaway root, the real tool run with --root.

Run with: python3 tools/knowledge/tests/test_stale.py
"""
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "stale"
failures, passes = [], 0
TODAY = date.today()


def root(*docs):
    tmp = Path(tempfile.mkdtemp())
    for rel, frontmatter in docs:
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + frontmatter + "\n---\n\nBody.\n")
    return tmp


def check(name, tmp, want_code, want_text=""):
    global passes
    r = subprocess.run([sys.executable, str(TOOL), "--root", str(tmp)], capture_output=True, text=True)
    if r.returncode == want_code and want_text in r.stdout + r.stderr:
        passes += 1
    else:
        failures.append(f"{name}: exit {r.returncode}, want {want_code} with '{want_text}'\n{r.stdout}{r.stderr}")


def dated(when):
    return f"review_after: {when}"


FIELDS = "type: Runbook\ntitle: \"A doc\"\ndescription: \"A doc.\"\nstatus: stable"

check("a missing root fails", root() / "missing", 1, "knowledge directory not found")
check("a root without knowledge fails", root(), 1, "knowledge directory not found")
empty = root()
(empty / "knowledge").mkdir()
check("an existing empty knowledge tree has no dated documents", empty, 0, "PASS: 0 documents reviewed")

check("today and later pass, undated docs ignored",
      root(("knowledge/operations/today.md", FIELDS + "\n" + dated(TODAY)),
           ("knowledge/references/later.md", FIELDS + "\n" + dated(TODAY + timedelta(days=90))),
           ("knowledge/policies/stable.md", FIELDS)),
      0, "PASS: 2 documents reviewed")

check("no dated document still passes",
      root(("knowledge/policies/stable.md", FIELDS)),
      0, "PASS: 0 documents reviewed")

passed = TODAY - timedelta(days=1)
check("a passed date is named with its date",
      root(("knowledge/operations/old.md", FIELDS + "\n" + dated(passed))),
      1, f"STALE knowledge/operations/old.md: review_after {passed} passed, review it and move the date")

check("a half-shaped date fails",
      root(("knowledge/operations/short.md", FIELDS + "\nreview_after: 2027-1-9")),
      1, "FAIL knowledge/operations/short.md: review_after '2027-1-9' is not a YYYY-MM-DD date")

check("an impossible month fails",
      root(("knowledge/operations/impossible.md", FIELDS + "\nreview_after: 2027-13-01")),
      1, "is not a YYYY-MM-DD date")

for failure in failures:
    print("FAIL:", failure)
print(f"{passes} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
