#!/usr/bin/env python3
# Spec: knowledge/operations/build-and-test.md
"""PostToolUse hook on Edit, MultiEdit, Write and NotebookEdit: the fast checks that apply to the edited file.

Silent with exit 0 when they pass; exit 2 with at most 15 lines (the rule and its fix) when not.
It also records the file for the Stop sign-off, and names the doc that covers it, once per session.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK_TIMEOUT_SECONDS = 2


def fail(reason, details=""):
    lines = [reason, *details.splitlines()]
    print("\n".join(line[:300] for line in lines[:15]), file=sys.stderr)
    sys.exit(2)


def run(*command):
    if not hasattr(os, "killpg"):
        fail("After-edit check deadlines require macOS, Linux or WSL.")
    try:
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, errors="replace", start_new_session=True)
    except OSError as error:
        fail(f"{command[0]} could not run: {error.strerror}")
    try:
        stdout, stderr = process.communicate(timeout=CHECK_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        # Descendants must not keep working after their checker times out.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        fail(f"{command[0]} timed out after {CHECK_TIMEOUT_SECONDS} seconds; verification is unavailable.")
    if process.returncode:
        fail(f"{command[0]} failed (exit {process.returncode}).", stderr or stdout)
    return stdout


try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    fail("After-edit could not read its input; verification is unavailable.")
if not isinstance(event, dict) or not isinstance(event.get("tool_input"), dict):
    fail("After-edit requires a tool_input object.")
session = event.get("session_id", "none")
if not isinstance(session, str) or not session or any(char in session for char in "/\\\0"):
    fail("After-edit requires a valid session identifier.")
# NotebookEdit names its file notebook_path.
file_path = event["tool_input"].get("file_path", event["tool_input"].get("notebook_path"))
if not isinstance(file_path, str) or not file_path or "\0" in file_path:
    fail("After-edit requires a nonempty file_path string.")
path = Path(file_path).resolve()
if ROOT not in path.parents or not path.is_file():
    sys.exit(0)
rel = path.relative_to(ROOT).as_posix()
problems = []

# Remember what this session edited: the Stop sign-off looks at these files only.
with (Path(tempfile.gettempdir()) / f"claude-edited-{session}").open("a") as f:
    f.write(rel + "\n")

# The knowledge base and the files agents read first.
if rel.startswith(("knowledge/", "work/")) or path.name in ("AGENTS.md", "CLAUDE.md"):
    output = run("tools/knowledge/knowledge-check")
    problems += [l for l in output.splitlines() if l.startswith("FAIL ")]

# Add your project's per-file checks here (formatter, linter), e.g. shellcheck for *.sh.

# Code a doc covers: name the doc, once per file and session.
hint = ""
if not rel.startswith(("knowledge/", "work/")) and path.suffix != ".md":
    # An uncovered file prints one empty line: no doc, no hint.
    docs = [doc for doc in run("tools/knowledge/doc-links", "--for", rel).splitlines() if doc]
    seen = Path(tempfile.gettempdir()) / f"claude-doc-hint-{session}"
    if docs and rel not in (seen.read_text().splitlines() if seen.exists() else []):
        with seen.open("a") as f:
            f.write(rel + "\n")
        hint = f"{rel} is covered by {', '.join(docs)}: update it if a documented fact changed."

if problems:
    fail(f"Checks after editing {rel}:", "\n".join(problems + ([hint] if hint else [])))
if hint:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": hint}}))
sys.exit(0)
