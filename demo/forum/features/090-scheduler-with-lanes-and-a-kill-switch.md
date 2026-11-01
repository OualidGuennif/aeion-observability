---
id: 090
title: "Scheduler with lanes and a kill switch"
area: build
size: L
parallel: true
depends_on: [089]
owner: builder
status: proposed
---

# 090 — Scheduler with lanes and a kill switch

**Goal.** Dispatch up to a work-in-progress limit, run `parallel: false` features alone, and stop everything from one switch without losing the queue.

## Scope

- Lane bookkeeping in the database with an advisory lock per worker.
- A WIP limit and an exclusivity rule for non-parallel features.
- A kill switch that stops new dispatch, drains nothing and marks the state.

## Out of scope

- Fair scheduling between users.
- Preempting a running build.

## Acceptance

- [ ] With the limit at two, a third feature waits until one finishes.
- [ ] A non-parallel feature runs only when the lane is empty.
- [ ] The switch stops dispatch within one tick and the queue is intact afterwards.

## Security

The switch is the documented emergency brake; its use is audited with the actor.

## Test

Run a mixed set through the scheduler with stub workers; assert the limits and the switch behaviour.
