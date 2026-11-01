---
id: 088
title: "Manifest validation"
area: build
size: M
parallel: true
depends_on: [087]
owner: builder
status: proposed
---

# 088 — Manifest validation

**Goal.** Validate the whole contract before any build: unique ids, known areas, dependencies that exist and always point backwards, and a slug per feature.

## Scope

- Cycle detection over the dependency graph with a readable error.
- A refusal for an unknown area, size or dependency.
- A comparison against `MANIFEST.json` so the file and the specs cannot drift.

## Out of scope

- Estimating build durations.
- Checking acceptance-test feasibility.

## Acceptance

- [ ] An injected cycle is reported as a path of ids.
- [ ] A forward dependency is refused.
- [ ] A stale manifest fails the check with the differing ids.

## Security

Validation runs before dispatch, so a malformed contract never reaches an agent.

## Test

Mutate the contract six ways and assert each refusal.
