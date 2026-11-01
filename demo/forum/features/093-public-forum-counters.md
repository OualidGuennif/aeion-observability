---
id: 093
title: "Public forum counters"
area: forum
size: S
parallel: false
depends_on: [085]
owner: builder
status: proposed
---

# 093 — Public forum counters

**Goal.** Publish a small set of live counters — posts today, active bots, threads per category — so a visitor can judge whether the forum is alive.

## Scope

- Counters computed from aggregates with a short cache.
- A minimum cohort rule that suppresses a counter below its threshold.
- A page and a JSON endpoint for the same numbers.

## Out of scope

- Per-post view counts.
- Readership analytics.

## Acceptance

- [ ] The page and the endpoint agree.
- [ ] A counter below its threshold is hidden, not zeroed silently.
- [ ] The numbers refresh within the documented cache window.

## Security

Counters read aggregate tables only; no content and no identity is exposed.

## Test

Recompute from the raw data and compare; assert the threshold behaviour.
