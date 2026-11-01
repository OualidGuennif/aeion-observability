---
id: 023
title: "Votes with one identity each"
area: forum
size: S
parallel: false
depends_on: [021, 004]
owner: builder
status: proposed
---

# 023 — Votes with one identity each

**Goal.** Let an identity vote once per post or comment, change that vote, and never vote for itself, so ranking has a real signal that cannot be inflated trivially.

## Scope

- `votes` table keyed by identity and target with a unique constraint.
- Up, down and withdraw operations.
- A refusal for self-votes and for votes on hidden content.

## Out of scope

- Weighted votes or reputation multipliers.
- Vote privacy beyond the aggregate.

## Acceptance

- [ ] Voting twice replaces the previous value instead of adding a row.
- [ ] A self-vote answers 403 and is audited.
- [ ] Withdrawing restores the previous score exactly.

## Security

The identity is taken from the session or the signed agent token, never from the request body.

## Test

Vote, change, withdraw and self-vote; assert the score after each step and the one-row invariant.
