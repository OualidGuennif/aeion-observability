---
id: 024
title: "Deterministic feed ranking"
area: forum
size: M
parallel: false
depends_on: [023]
owner: builder
status: proposed
---

# 024 — Deterministic feed ranking

**Goal.** Rank a channel's feed with a documented formula over recency, score and reply count, so the ordering is reproducible and explainable without a model.

## Scope

- A scoring function in one module with its constants named and documented.
- A query that pages by score then id, with a stable tie-break.
- A debug view showing each post's score components to administrators only.

## Out of scope

- Personalized or learned ranking.
- A/B testing of the formula.

## Acceptance

- [ ] The same data yields the same order on two runs.
- [ ] A one-hour-old post with ten votes outranks a ten-hour-old post with one.
- [ ] Changing a constant changes the order in a test that pins both.

## Security

The score never uses hidden moderation state in a way the debug view cannot explain.

## Test

Pin a dataset, run the ranking twice, assert equality; vary a constant and assert a pinned order change.
