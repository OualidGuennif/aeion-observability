---
id: 078
title: "Category quotas and mix"
area: corpus
size: S
parallel: false
depends_on: [076]
owner: builder
status: proposed
---

# 078 — Category quotas and mix

**Goal.** Fix the share of each category in a day's seeding — a third each, within tolerance — so one category cannot dominate the forum.

## Scope

- A quota configuration per category and a per-day counter.
- A picker that chooses the category before the item, respecting the remaining quota.
- A tolerance that absorbs an empty category without breaking the day.

## Out of scope

- Personalized category mixes.
- Trend detection.

## Acceptance

- [ ] A day with all categories available lands within the tolerance of a third each.
- [ ] An empty category is compensated by the others, not left as a gap.
- [ ] The counters reset at midnight.

## Security

The picker reads only category counters and ids.

## Test

Simulate a day with three and with two populated categories; assert the mixes.
