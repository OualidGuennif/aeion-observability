---
id: 098
title: "Load test with a latency budget"
area: ops
size: S
parallel: false
depends_on: [034]
owner: builder
status: proposed
---

# 098 — Load test with a latency budget

**Goal.** Drive fifty concurrent readers against a seeded instance and pin a p95 budget per route, so performance is a number the build can fail on.

## Scope

- A script with a fixed request mix and a warm-up phase.
- Budgets per route class, recorded next to the script.
- A failure exit when a budget is exceeded.

## Out of scope

- Distributed load generation.
- Capacity planning.

## Acceptance

- [ ] The script reports p50, p95 and p99 per route class.
- [ ] Exceeding a budget exits non-zero with the route named.
- [ ] The numbers are reproducible within the documented tolerance.

## Security

The script targets a disposable instance and refuses a host it does not recognise as local.

## Test

Run against a seeded instance and assert the report shape and the exit code on a tightened budget.
