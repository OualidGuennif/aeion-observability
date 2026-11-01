---
name: pr-taste
description: Turns the owner's pull request comments into durable preferences in knowledge/policies/owner-preferences.md, and checkable ones into hookify rules. Use after the owner comments on a pull request, and weekly.
---

# Capture the owner's taste

1. Read the owner's comments since the newest entry date: `gh api "repos/{owner}/{repo}/issues/comments?since=<date>" --paginate` and `gh api "repos/{owner}/{repo}/pulls/comments?since=<date>" --paginate`, keeping `OWNER_LOGIN`.
2. Keep what lasts (architecture, naming, style, security, UI, workflow), not one-off fixes: `- <preference> (PR #n, YYYY-MM-DD)` under its heading. A later preference replaces an earlier one: say so.
3. Checkable (a forbidden pattern, a required header): a warn rule `.claude/hookify.<name>.local.md` when `hookify` is installed; otherwise under "Checkable, no hook yet".
4. Never record a secret, private data, or anything the owner did not say.
5. Commit on a task branch, open a PR, skill `pr-review`.

## Avoid overgeneralizing a correction
Separate an explicit durable preference from a one-off request, an inferred taste and a rule
limited to one component. Record the original scope and evidence without private transcript
content. A new hook needs a reproducible positive and negative case; start with a warning and
measure noise. Do not turn a reviewer nit into a repository-wide prohibition.
