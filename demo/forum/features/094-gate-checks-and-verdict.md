---
id: 094
title: "Gate checks and verdict"
area: build
size: M
parallel: true
depends_on: [093]
owner: builder
status: proposed
---

# 094 — Gate checks and verdict

**Goal.** Run the repository checks in a fresh sandbox against the built tree, and write one deterministic verdict the policy can trust.

## Scope

- The check set: unit tests, doc-links, knowledge-check, repo-health, the app's own suite.
- A sandboxed run with stdin-fed sources and a fresh sandbox for the result.
- A verdict object: pass or fail, per-check status, duration, artifact digest.

## Out of scope

- Fixing failures automatically.
- Running the whole CI matrix locally.

## Acceptance

- [ ] A failing check yields a fail verdict with the check named.
- [ ] The verdict records the artifact digest it was computed on.
- [ ] The build workspace is never used to run checks.

## Security

Checks run in a fresh sandbox; a compromised build cannot edit its own verdict.

## Test

Run a passing and a failing tree; assert the verdicts and the digests.
