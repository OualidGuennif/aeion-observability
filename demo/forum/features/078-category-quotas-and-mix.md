---
id: 078
title: "Category quotas and mix"
area: corpus
size: S
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [076]
owner: builder
status: proposed
---

# 078 — Category quotas and mix

## Intent

Fix the share of each category in a day's seeding — a third each, within tolerance — so one category cannot dominate the forum.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- Pin a daily target of one third per category with 5 percentage point tolerance on a fixed 300-selection simulation.
- Choose category before item, transactionally counting selections with a seeded tie-break.
- If a category is empty, redistribute among available categories and record degraded coverage; empty-all refuses dispatch.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The picker reads only category counters and ids.

This invariant and the acceptance cases belong to planned protected check `agora-078`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A day with all categories available lands within the tolerance of a third each.
- [ ] An empty category is compensated by the others, not left as a gap.
- [ ] The counters reset at midnight.

**Test scenario:** Simulate a day with three and with two populated categories; assert the mixes.

## Out of scope

- Personalized category mixes.
- Trend detection.
