---
id: 053
title: "Moderation audit trail"
area: moderation
size: S
parallel: false
depends_on: [009]
owner: builder
status: proposed
---

# 053 — Moderation audit trail

**Goal.** Route every moderation action through the hash-chained log with a stable action code, so the history of a post can be reconstructed and verified.

## Scope

- Action codes covering hold, approve, reject, lock, sanction, appeal and override.
- A per-target history view for moderators.
- A verifier run in the nightly check.

## Out of scope

- Exporting the trail to a third party.
- Storing post text in the trail.

## Acceptance

- [ ] A post held then restored shows exactly two entries in order.
- [ ] The chain verifies after a restart.
- [ ] No entry contains body text.

## Security

The application role keeps INSERT-only rights on the audit table.

## Test

Apply a sequence of actions and assert the entries, their order and the verifier.
