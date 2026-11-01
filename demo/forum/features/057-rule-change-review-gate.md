---
id: 057
title: "Rule change review gate"
area: moderation
size: S
parallel: false
depends_on: [041]
owner: builder
status: proposed
---

# 057 — Rule change review gate

**Goal.** Make a rule change a reviewed commit with a fixture diff, so a rule cannot be loosened to let a specific post through.

## Scope

- A check that the rules file changed together with a test or a fixture diff.
- A rendered diff of the public rules page in the pull request body.
- A refusal to ship a code removal that old posts cite.

## Out of scope

- Approval workflows inside the app.
- Versioned rule branches.

## Acceptance

- [ ] A rules change without a fixture or test change fails the check.
- [ ] The pull request body shows the rendered diff.
- [ ] Removing a cited code is refused.

## Security

The gate runs in CI, before merge, on the same repository the orchestrator cannot merge outside the allowlist.

## Test

Change the rules alone and assert failure; change with a fixture and assert pass.
