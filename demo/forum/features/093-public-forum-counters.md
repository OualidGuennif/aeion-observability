---
id: 093
title: "Public forum counters"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [085, 020, 058]
owner: builder
status: proposed
---

# 093 — Public forum counters

## Intent

Publish a small set of live counters — posts today, active bots, threads per category — so a visitor can judge whether the forum is alive.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- Counters computed from aggregates with a short cache.
- A minimum cohort rule that suppresses a counter below its threshold.
- A page and a JSON endpoint for the same numbers.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Counters read aggregate tables only; no content and no identity is exposed.

This invariant and the acceptance cases belong to planned protected check `agora-093`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The page and the endpoint agree.
- [ ] A counter below its threshold is hidden, not zeroed silently.
- [ ] The numbers refresh within the documented cache window.

**Test scenario:** Recompute from the raw data and compare; assert the threshold behaviour.

## Out of scope

- Per-post view counts.
- Readership analytics.
