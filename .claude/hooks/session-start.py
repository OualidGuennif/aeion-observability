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


def capped(items):
    """At most six lines: every item, or the first five and how many were left out."""
    shown = items if len(items) <= 6 else items[:5] + [f"… and {len(items) - 5} more"]
    return ["  " + item[:110] for item in shown]


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
    # The flow mode decides whether work ends in a reviewed push or a local commit; local unless set to team.
    if out("git", "config", "--local", "--get", "aeion.mode") != ["team"]:
        lines.append("Æion Factory mode: local (git lifecycle off: no develop, review, PR or release gate; "
                     "safety guards stay on). Team flow: README.md#team-git-flow")
    else:
        branch = " ".join(out("git", "branch", "--show-current")) or "a detached HEAD"
        lines.append(f"Æion Factory mode: team on {branch} "
                     "(develop: review before each push; main: release PR). Local: git config --unset aeion.mode")
        # Team work happens on develop; main moves only through the release pull request.
        if branch == "main":
            lines.append("branch: main; team work happens on develop (git switch develop)")
        # The pre-commit checks and the pre-push review gate run only when git uses the repository's hooks.
        hooks = out("git", "config", "--path", "--get", "core.hooksPath")
        if not hooks or (ROOT / hooks[0]).resolve() != (ROOT / "tools/git-hooks").resolve():
            lines.append("git hooks: off; enable with git config core.hooksPath tools/git-hooks")
    # Uncommitted changes: one you cannot explain is not yours.
    status = out("git", "status", "--short")
    lines.append(f"git status: {len(status)} changed path(s)" if status else "git status: clean")
    lines += capped(status)
    # The last commits.
    lines.append("last commits:")
    lines += ["  " + s for s in out("git", "log", "-5", "--oneline")]
# Open tasks.
work = ROOT / "work/current.md"
titles = [l[3:] for l in work.read_text(encoding="utf-8").split("\n") if l.startswith("## ")] if work.exists() else []
lines.append(f"work/current.md: {len(titles)} open task(s)")
lines += capped(titles)
# The scorecard always shows; the lists above give way to it within the 25 lines.
score = out("tools/repo-health/repo-health")[:25]
print("\n".join(lines[:25 - len(score)] + score))
