---
id: 047
title: "Appeals"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [046, 008, 043]
owner: builder
status: proposed
---

# 047 — Appeals

## Intent

Let an author appeal a decision once, with the reason code attached, and require a different moderator to decide, so a decision is checked rather than repeated.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- `appeals` table linked to one moderation action and one author.
- A rule that the deciding moderator differs from the original one.
- Outcomes: upheld, overturned, or escalated to the administrator.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Appeals are rate limited per author and audited like any other action.

This invariant and the acceptance cases belong to planned protected check `agora-047`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A second appeal on the same action answers 409.
- [ ] The original moderator cannot decide the appeal.
- [ ] An overturned appeal restores the content in the same transaction.

**Test scenario:** File two appeals, attempt self-review, then overturn and assert visibility restored.

## Out of scope

- Appeals against bans by non-authors.
- Multiple appeal rounds on the same action.
