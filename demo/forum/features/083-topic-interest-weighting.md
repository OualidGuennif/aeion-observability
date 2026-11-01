---
id: 083
title: "Topic interest weighting"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [060, 076, 078]
owner: builder
status: proposed
---

# 083 — Topic interest weighting

## Intent

Use reviewed finite category weights with seeded selection and quota availability; qualify the fixed three-category distribution without claiming distinct arbitrary random draws.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- Use the category-weight fields already declared by 060; normalize finite nonnegative weights and reject an all-zero vector.
- Use a seeded weighted picker; quota availability from 078 bounds which categories are eligible.
- With suitable available items and positive combined weights, the fixed 300-selection daily fixture covers exactly the three schema categories.

**required_categories:** tech, state, government.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Weights are configuration; they never come from user input.

This invariant and the acceptance cases belong to planned protected check `agora-083`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A zero tech weight excludes tech for that persona; missing eligible categories produce an explicit degraded result.
- [ ] Two pinned contrasting personas and a fixed seed produce the pre-registered category counts; no universal promise of different random draws.
- [ ] The daily fixed fixture covers tech, state and government; an unknown fourth category is rejected by the shared schema.

**Test scenario:** Draw a day for three personas and assert the distributions and the diversity check.

## Out of scope

- Learning weights from engagement.
- Per-user interests.
