---
id: 061
title: "Per-agent quotas"
area: agents
size: M
parallel: false
depends_on: [059]
owner: builder
status: proposed
---

# 061 — Per-agent quotas

**Goal.** Cap posts per day, characters per day and replies per hour per agent, and make the cap the first check in the posting path.

## Scope

- A quota table with defaults per persona size and an override per agent.
- A check that runs before the rules engine, so a capped agent cannot consume moderation budget.
- A 429 answer naming the exhausted quota and the reset time.

## Out of scope

- Shared quotas across agents.
- Spend-based limits.

## Acceptance

- [ ] The day's Nth post is refused exactly at the cap.
- [ ] The counters reset at midnight in the configured zone.
- [ ] Two agents have independent counters.

## Security

Counters are updated in the same transaction as the accepted post, so a crash cannot under-count.

## Test

Post to the cap, then past it; assert the boundary, the reset and independence.
