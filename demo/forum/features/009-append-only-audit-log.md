---
id: 009
title: "Append-only audit log"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [002]
owner: builder
status: proposed
---

# 009 — Append-only audit log

## Intent

Record every privileged action in a hash-chained table with a verifier, so tampering with history is detectable without trusting the application.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- `audit` table with sequence, actor, action code, target, outcome, previous hash and entry hash.
- A single write path that refuses updates and deletes at the database role level.
- A `verify` command that walks the chain and reports the first break.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The application audit writer has INSERT only; a separate restricted verifier can SELECT. Serialize predecessor/hash allocation with a database lock inside the same transaction as the privileged mutation.

This invariant and the acceptance cases belong to planned protected check `agora-009`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Editing one row makes `verify` fail at that sequence.
- [ ] A failed action is audited with its outcome, not dropped.
- [ ] The chain survives a restart.

**Test scenario:** Run concurrent appends and action rollbacks; assert one verifiable chain with no fork, committed outcomes, restart survival, and UPDATE/DELETE denial. Tamper only through a disposable test administrator.

## Out of scope

- Log shipping to a third party.
- Content capture: audit records codes and identifiers, not text.
