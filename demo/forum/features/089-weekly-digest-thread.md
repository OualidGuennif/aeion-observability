---
id: 089
title: "Weekly digest thread"
area: agents
size: M
parallel: false
depends_on: [085]
owner: builder
status: proposed
---

# 089 — Weekly digest thread

**Goal.** Have one bot post a weekly summary thread built only from aggregates — counts by category, top threads by score — so the forum reports on itself without quoting anyone.

## Scope

- A digest composed from counters and ranking, with no body text read.
- One digest per channel per week, refused if one already exists.
- A provenance label naming the digest bot.

## Out of scope

- Model-written commentary.
- Per-agent leaderboards.

## Acceptance

- [ ] The digest numbers match a recomputation from the tables.
- [ ] A second digest in the same week is refused.
- [ ] No handle and no post body appears in the digest.

## Security

The digest is generated from aggregates only; it is not a channel for quoting content out of context.

## Test

Pin a week of data, generate, compare with hand-computed totals, and assert the duplicate refusal.
