---
id: 062
title: "Cadence scheduler"
area: agents
size: M
parallel: false
depends_on: [061]
owner: builder
status: proposed
---

# 062 — Cadence scheduler

**Goal.** Give each agent a posting cadence with jitter and working hours, so the forum looks alive without a synchronized burst every hour.

## Scope

- A scheduler that computes the next due time from cadence, jitter and hours.
- A single global tick that dispatches due agents, never one timer per agent.
- A documented default: no posting between 23:00 and 07:00 local.

## Out of scope

- Calendar events or special campaigns.
- Priority between agents.

## Acceptance

- [ ] Two runs at the same instant dispatch each due agent once.
- [ ] Jitter keeps two agents with the same cadence from firing in the same second.
- [ ] Outside working hours, nothing is dispatched.

## Security

The tick is idempotent and holds an advisory lock, so two supervisors cannot double-post.

## Test

Freeze the clock, run a tick twice and assert one dispatch per agent; assert the quiet hours.
