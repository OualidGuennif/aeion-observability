---
id: 097
title: "Observer agent with bounded powers"
area: orchestrator
size: L
parallel: false
depends_on: [095]
owner: builder
status: proposed
---

# 097 — Observer agent with bounded powers

**Goal.** Run one Flue agent that watches the queue, triages failures into issues, proposes pull requests and reports to the owner — with no ability to merge outside the allowlist or change protections.

## Scope

- A tool surface: read queue and traces, open issues, open pull requests, comment with evidence.
- An explicit denylist: merge outside the allowlist, branch protection, secrets, deploy files.
- A run budget, a step cap and a kill switch shared with the scheduler.

## Out of scope

- Direct pushes to `develop` or `main`.
- Rotating credentials or editing CI.

## Acceptance

- [ ] An attempted merge outside the allowlist is refused and audited.
- [ ] A failed build produces one issue, deduplicated against an open one.
- [ ] The agent cannot call a tool outside its surface, proven by a negative test.

## Security

Least privilege: the observer's token is scoped to issues and pull requests, not to repository administration.

## Test

Replay three scenarios — failure, success, forbidden merge — and assert the actions and refusals.
