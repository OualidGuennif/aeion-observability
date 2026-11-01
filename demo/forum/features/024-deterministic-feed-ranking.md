---
id: 024
title: "Deterministic feed ranking"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [023, 022]
owner: builder
status: proposed
---

# 024 — Deterministic feed ranking

## Intent

Rank a channel's feed with a documented formula over recency, score and reply count, so the ordering is reproducible and explainable without a model.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- A scoring function in one module with its constants named and documented.
- A query that pages by score then id, with a stable tie-break.
- A debug view showing each post's score components to administrators only.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The score never uses hidden moderation state in a way the debug view cannot explain.

This invariant and the acceptance cases belong to planned protected check `agora-024`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The same data yields the same order on two runs.
- [ ] A one-hour-old post with ten votes outranks a ten-hour-old post with one.
- [ ] Changing a constant changes the order in a test that pins both.

**Test scenario:** Pin a dataset, run the ranking twice, assert equality; vary a constant and assert a pinned order change.

## Out of scope

- Personalized or learned ranking.
- A/B testing of the formula.
