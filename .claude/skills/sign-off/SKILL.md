---
name: sign-off
description: The checklist that ends a task before it is pushed - tests, docs and their links, the changelog line, the task state, the AGENTS.md map, a security scan on sensitive diffs, and a recorded review. Use at the end of every task.
---

# Sign off

## Overview
Done means proven and documented, not "the code is written". Reasons: `AGENTS.md`, definition of done.

## Process
1. The tests for what changed (the project's commands in `AGENTS.md`).
2. `tools/knowledge/doc-links --diff origin/develop --worktree` (`origin/main` without a develop branch; skipped without git): for each L3, update the doc (skill `okf-update`) or add `Docs-Checked: knowledge/<doc>.md -- <why no fact changed>` to a commit message.
3. `CHANGELOG.md`: a line under `## [Unreleased]` for what users will notice. `work/current.md`: update the task's entry, or delete it when done.
4. `AGENTS.md`: when a top-level folder, a command or a rule changed.
5. A sensitive diff (auth, infrastructure, CI, secrets): skill `security-scan` on the changes.
   Match each completion claim to fresh relevant command output and its exit status. A model's
   report, partial check or stale result is not verification; inspect the actual diff/artifact.
   Update the architecture spec when its facts change. After committing, run
   `tools/architecture/refresh --target HEAD --base origin/develop` before pushing.
6. Skill `pr-review` on `origin/develop..HEAD`, then push `develop`; its verdict lists the checks run. A release goes through skill `ship`. Without git: the tests and docs are the whole sign-off.

## Red flags
"Tests pass" without the command; a PR body that lists no checks; a doc left for "later".

## Verification
- [ ] Each check above ran, with its result in the review's checks line.
- [ ] `doc-links --diff` passes.

## Report only what the evidence supports
Inspect the final working diff, staged changes and new files so omitted artifacts do not hide
behind a clean `git diff`. Check that requested behavior, compatibility and meaningful refusal
paths are covered. Summarize what changed, why, exact checks and unverified runtime/host limits.

A syntax pass is not a behavioral qualification; a synthetic replay is not production evidence.
Distinguish local assessment from independent review and installed configuration from trusted
activation. If no push/release was authorized, stop at local delivery after the appropriate
checks rather than performing step 6 automatically. No automatic agent launch is part of sign-off.
