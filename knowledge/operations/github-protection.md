---
type: Runbook
title: "GitHub main protection"
description: "Required pull requests and real CI checks on main, including administrators, and how to verify adopted repositories."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.2
  at: 2026-10-25
---

# GitHub main protection

Repository files do not impose GitHub settings. At adoption, an administrator must configure
branch protection/rulesets for main, then read the effective result back through the API.

Require pull requests, branches up to date with main, the repository's actual CI job names and
resolved conversations; allow merge commits and do not require linear history, because a release
pull request `develop → main` merges with a merge commit so `develop` stays an ancestor of `main`
(owner decision, 2026-10-28). Enforce these rules for administrators; disallow
force-push and branch deletion. Preserve stronger existing rules. Pin required checks to their
actual GitHub App where available; do not invent check names or require disabled optional jobs.

Æion Factory requires Knowledge/links/health, Graphify/Archify, secret-scan, dependency-scan and
sast-scan. The fresh `Review: OK` comment remains required by the delivery workflow; it is not
an approving forge review. The solo-owner workflow uses zero required human approvals, rather
than making the author approve their own PR. This distinction is explicit: CI/PR requirements
are server-enforced; the comment verdict is a reviewed procedure.

On 2026-10-25, main protection was applied and re-read for OualidGuennif's aeion-factory,
aeion-spaceship, aeion-playground, aeion-croa, aeion-ops, aeion-observability and aeion-website.
Each uses its own observed CI names. Playground's existing restrictions were preserved and its
additional product/telemetry jobs added. No production deployment setting was changed.

Verify after configuration changes (substitute the actual repository):

```bash
gh api repos/OWNER/REPO/branches/main --jq '{name,protected}'
gh api repos/OWNER/REPO/branches/main/protection
gh api repos/OWNER/REPO/rulesets
```

A protection update must preserve existing restrictions, bypass policies and required signatures
unless the owner explicitly changes them. Save before/after evidence locally. Never temporarily
remove protection to push or merge. Fix a failing required check through a PR.
