---
id: 089
title: "Dependency queue"
area: build
size: M
parallel: true
depends_on: [088]
owner: builder
status: proposed
---

# 089 — Dependency queue

**Goal.** Accept one or many feature ids, store them as a queue with states, and expose the next runnable set in dependency order.

## Scope

- A queue table with feature id, state, timestamps and the run id when started.
- A `next()` that returns every feature whose dependencies are all built.
- Enqueue of ten ids in one request, refusing unknown or duplicate ids.

## Out of scope

- Priority preemption.
- Editing the contract from the queue.

## Acceptance

- [ ] Enqueuing ten independent features returns all ten in id order.
- [ ] A feature whose dependency is queued but not built is not returned.
- [ ] A duplicate enqueue is a no-op with a 200.

## Security

The queue is writable only by the cockpit session and the orchestrator; both audited.

## Test

Enqueue a chain and a parallel set; assert the returned order at each step.
