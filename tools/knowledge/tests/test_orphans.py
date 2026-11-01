#!/usr/bin/env python3
"""Fixture tests for tools/knowledge/orphans: a throwaway root, the real tool run with --root.

Run with: python3 tools/knowledge/tests/test_orphans.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "orphans"
failures, passes = [], 0
INDEX = "# Knowledge\n\n- [Policies](policies/index.md)\n- [A doc](a.md)\n"


def root(files):
    tmp = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return tmp


def check(name, tmp, want_code, want_text=""):
    global passes
    r = subprocess.run([sys.executable, str(TOOL), "--root", str(tmp)], capture_output=True, text=True)
    if r.returncode == want_code and want_text in r.stdout + r.stderr:
        passes += 1
    else:
        failures.append(f"{name}: exit {r.returncode}, want {want_code} with '{want_text}'\n{r.stdout}{r.stderr}")


BASE = {
    "knowledge/index.md": INDEX,
    "knowledge/a.md": "# A\n",
    "knowledge/policies/index.md": "# Policies\n\n- [Rule](rule.md)\n",
    "knowledge/policies/rule.md": "# Rule\n",
}

check("a missing root fails", root({}) / "missing", 1, "knowledge directory not found")
check("a root without knowledge fails", root({}), 1, "knowledge directory not found")
empty = root({})
(empty / "knowledge").mkdir()
check("a knowledge tree without its entry index fails", empty, 1, "knowledge index not found")
check("an index-only knowledge tree is valid", root({"knowledge/index.md": "# Knowledge\n"}),
      0, "PASS: 1 documents reachable")

check("index to folder index to document reaches all three",
      root(BASE), 0, "PASS: 4 documents reachable")

orphan = dict(BASE, **{"knowledge/notes/lost.md": "# Lost\n"})
check("a document nothing links is an orphan",
      root(orphan), 1, "FAIL knowledge/notes/lost.md: orphan, link it from knowledge/index.md or the folder index")

check("a link from another document counts",
      root(dict(BASE, **{"knowledge/a.md": "# A\n\nSee [B](b.md).\n", "knowledge/b.md": "# B\n"})),
      0, "PASS: 5 documents reachable")

check("a frontmatter source counts",
      root(dict(BASE, **{"knowledge/a.md": "---\ntype: Reference\ntitle: \"A\"\ndescription: \"A.\"\n"
                                            "status: draft\nsources:\n  - resource: b.md\n---\n\n# A\n",
                         "knowledge/b.md": "# B\n"})),
      0, "PASS: 5 documents reachable")

check("a link from outside knowledge does not count",
      root(dict(orphan, **{"work/current.md": "# Work\n\n[Lost](../knowledge/notes/lost.md)\n"})),
      1, "FAIL knowledge/notes/lost.md: orphan")

check("a document reached only from an orphan stays an orphan",
      root(dict(orphan, **{"knowledge/notes/lost.md": "# Lost\n\n[B](b.md)\n", "knowledge/notes/b.md": "# B\n"})),
      1, "FAIL knowledge/notes/b.md: orphan")

for failure in failures:
    print("FAIL:", failure)
print(f"{passes} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
