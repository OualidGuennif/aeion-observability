#!/usr/bin/env python3
# Spec: knowledge/operations/build-and-test.md
"""Stop hook: before an agent stops, the docs its change touches are current (the sign-off).

Input: the Stop event on stdin. Only the files this session edited count (after-edit.py records
them). When one of them is code whose covering doc did not change (tools/knowledge/doc-links L3),
work/current.md did not change, or it opened a new top-level folder without AGENTS.md changing, it
blocks with the findings not shown yet in this session; a second stop always passes. Local mode
(git config aeion.mode local) always passes.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/hooks"))
from project_files import git_active  # noqa: E402 - the shared repository test, beside this hook.

DOC_PREFIXES = ("knowledge/", "work/", ".claude/", "tech-watch/")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


# A reminder, not a guard: unreadable input or an unusable session id has nothing recorded to check.
try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    sys.exit(0)
if not isinstance(event, dict) or event.get("stop_hook_active"):
    sys.exit(0)
# A plain folder, even one nested in another repository, has no branch to compare; a broken one is
# reported by session-start, and this reminder must not send the agent after a check that cannot run.
try:
    if not git_active(ROOT):
        sys.exit(0)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
# Local play (git config aeion.mode local) has no task-closure ritual to remind of.
if git("config", "--local", "--get", "aeion.mode").stdout.strip() == "local":
    sys.exit(0)
session = event.get("session_id", "none")
if not isinstance(session, str) or not session or any(char in session for char in "/\\\0"):
    sys.exit(0)
edited_log = Path(tempfile.gettempdir()) / f"claude-edited-{session}"
edited = set(edited_log.read_text().splitlines()) if edited_log.exists() else set()
if not edited:
    sys.exit(0)

# The base is where this branch left develop (or main without one); on it, only unpushed work counts.
base = next((git("merge-base", "HEAD", ref).stdout.strip() for ref in ("origin/develop", "develop", "origin/main", "main")
             if git("rev-parse", "--verify", "--quiet", ref).returncode == 0), "")
if not base:
    sys.exit(0)
changed = set(git("diff", "--name-only", "-z", f"{base}...HEAD").stdout.split("\0")) - {""}
changed |= set(git("diff", "--name-only", "-z", "HEAD").stdout.split("\0")) - {""}
changed |= set(git("ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0")) - {""}
code = sorted(p for p in changed & edited if not p.startswith(DOC_PREFIXES) and not p.endswith(".md"))
if not code:
    sys.exit(0)

findings = []
links = subprocess.run([sys.executable, str(ROOT / "tools/knowledge/doc-links"), "--diff", base, "--worktree"],
                       cwd=ROOT, capture_output=True, text=True, check=False)
# L1 names path:line, L2 the doc, L3 the changed file: keep the ones about this session's files.
findings += [line for line in links.stdout.splitlines() if any(
    line.startswith((f"RULE L1 {path}:", f"RULE L2 {path}:", f"RULE L3 {path} changed,"))
    for path in set(code) | edited)]
if links.returncode and not any(line.startswith("RULE L") for line in links.stdout.splitlines()):
    findings.append("doc-links could not verify this change: run it directly and resolve the check error.")
if "work/current.md" not in changed:
    findings.append("work/current.md did not change: update the task's entry, or delete it if the task is done.")
# The release notes are written as the work lands, not reconstructed at release time.
if (ROOT / "CHANGELOG.md").exists() and "CHANGELOG.md" not in changed:
    findings.append("CHANGELOG.md did not change: add a line under '## [Unreleased]' for what users will notice.")
base_top = {p.split("/")[0] for p in git("ls-tree", "--name-only", "-z", base).stdout.split("\0") if p}
new_top = sorted({p.split("/")[0] for p in code if "/" in p} - base_top)
if new_top and "AGENTS.md" not in changed:
    findings.append(f"new top-level {', '.join(new_top)} but AGENTS.md (repository map) did not change.")
if not findings:
    sys.exit(0)

# Each finding is shown once per session, so a long task is reminded, never looped.
seen_log = Path(tempfile.gettempdir()) / f"claude-sign-off-{session}"
seen = set(seen_log.read_text().split()) if seen_log.exists() else set()
digest = lambda line: hashlib.sha256(line.encode()).hexdigest()[:16]
fresh = [l for l in findings if digest(l) not in seen]
if not fresh:
    sys.exit(0)
with seen_log.open("a") as f:
    f.write("".join(digest(l) + "\n" for l in fresh))
reason = ("Sign-off before stopping: " + str(len(code)) + " code file(s) you edited changed since the base branch.\n"
          + "\n".join(fresh[:10])
          + "\nUpdate them (skill okf-update), or say in your answer why no documented fact changed.")
print(json.dumps({"decision": "block", "reason": reason}))
sys.exit(0)
