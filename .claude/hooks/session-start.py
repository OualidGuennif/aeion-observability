#!/usr/bin/env python3
# Spec: knowledge/operations/build-and-test.md
"""SessionStart hook: at most 25 lines of facts — the flow mode, uncommitted changes, recent commits,
open tasks and the health scorecard — so a new or resumed session starts from evidence."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/hooks"))
from project_files import git_active  # noqa: E402


def out(*command):
    return [l for l in subprocess.run(command, cwd=ROOT, capture_output=True, text=True).stdout.split("\n") if l.strip()]


lines = []
lines += ["Bounded intake: full reads/dumps above 64 KiB or 400 lines are refused.",
          "Use targeted Read ranges, limited searches and summaries; see knowledge/policies/bounded-intake.md."]
try:
    repository = git_active(ROOT)
except subprocess.SubprocessError:
    repository = None
if repository is None:
    lines.append("git: this folder has a .git that git cannot read; repair it before any commit.")
elif not repository:
    # A plain folder: no branch, pull request, review, CI or tag; done means the tests pass.
    lines.append("git: inactive (plain folder); the branch, review, CI and release flow is skipped.")
else:
    # The flow mode decides whether work ends in a reviewed push or a local commit.
    if out("git", "config", "--local", "--get", "aeion.mode") == ["local"]:
        lines.append("Æion Factory mode: local (commits on main, no PR/CI/task-state ritual; safety guards stay on). "
                     "Team flow: git config --unset aeion.mode")
    else:
        lines.append(f"Æion Factory mode: team on {' '.join(out('git', 'branch', '--show-current')) or 'a detached HEAD'} "
                     "(develop: review before each push; main: release PR). Local play: git config aeion.mode local")
    # Uncommitted changes: one you cannot explain is not yours.
    status = out("git", "status", "--short")
    lines.append(f"git status: {len(status)} changed path(s)" if status else "git status: clean")
    lines += ["  " + s for s in status[:6]]
    # The last commits.
    lines.append("last commits:")
    lines += ["  " + s for s in out("git", "log", "-5", "--oneline")]
# Open tasks.
work = ROOT / "work/current.md"
titles = [l[3:] for l in work.read_text(encoding="utf-8").split("\n") if l.startswith("## ")] if work.exists() else []
lines.append(f"work/current.md: {len(titles)} open task(s)")
lines += ["  " + t[:110] for t in titles[:6]]
# The scorecard.
lines += out("tools/repo-health/repo-health")
print("\n".join(lines[:25]))
