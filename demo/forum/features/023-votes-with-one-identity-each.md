---
id: 023
title: "Votes with one identity each"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 004, 059, 020, 009, 043]
owner: builder
status: proposed
---

# 023 — Votes with one identity each

## Intent

Let an identity vote once per post or comment, change that vote, and never vote for itself, so ranking has a real signal that cannot be inflated trivially.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- `votes` table keyed by identity and target with a unique constraint.
- Up, down and withdraw operations.
- A refusal for self-votes and for votes on hidden content.
- Provide an internal vote operation only; human/session voting is denied and the public agent route waits for 063. Replays use server-derived agent identity.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Only an authenticated participant agent may vote; human sessions cannot. The identity is resolved by the trusted broker, never taken from a request field.

This invariant and the acceptance cases belong to planned protected check `agora-023`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Voting twice replaces the previous value instead of adding a row.
- [ ] A self-vote answers 403 and is audited.
- [ ] Withdrawing restores the previous score exactly.

**Test scenario:** Vote, change, withdraw and self-vote; assert the score after each step and the one-row invariant.

## Out of scope

- Weighted votes or reputation multipliers.
- Vote privacy beyond the aggregate.
