---
id: 024
sequence: 36
title: "Deterministic feed ranking"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [023, 022]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 024 — Deterministic feed ranking

## Intent

Rank a channel's feed with a documented formula over recency, score and reply count, so the ordering is reproducible and explainable without a model.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Write the pure feed-score function with named constants.
2. Apply visibility first and sort by score with an explicit stable tie-break.
3. Pin ordering, reference time and a controlled constant-change fixture.

**Scope:**

- A scoring function in one module with its constants named and documented.
- A query that pages by score then id, with a stable tie-break.
- A debug view showing each post's score components to administrators only.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
