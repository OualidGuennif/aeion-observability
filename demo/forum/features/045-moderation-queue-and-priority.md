---
id: 045
title: "Moderation queue and priority"
area: moderation
size: M
parallel: false
depends_on: [044]
owner: builder
status: proposed
---

# 045 — Moderation queue and priority

**Goal.** Order the queue by rule severity, report count and age with a stable tie-break, so the worst content is seen first and nothing starves.

## Scope

- A queue query computing a priority from severity, distinct reporters and age.
- A starvation guard that lifts old items after a documented threshold.
- A view showing the components behind each item's position.

## Out of scope

- Assignment to individual moderators.
- SLA timers or escalation by clock.

## Acceptance

- [ ] A high-severity item outranks a low-severity one filed earlier.
- [ ] An old low-severity item eventually outranks a fresh one.
- [ ] Two items with equal components order by id, stably.

## Security

The queue is visible only to moderators; its query is covered by the permission matrix.

## Test

Build a fixture with mixed severities and ages; assert the order and the starvation lift.
