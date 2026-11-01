---
id: 074
title: "Ten-agent dry run"
area: agents
size: M
parallel: false
depends_on: [063]
owner: builder
status: proposed
---

# 074 — Ten-agent dry run

**Goal.** Simulate an hour with ten agents against the seed, with fake inference, and assert quotas, diversity and zero containment escapes.

## Scope

- A harness that drives the scheduler with a frozen clock and a stub model.
- Invariants asserted at the end: no quota exceeded, no forbidden tool reached, no duplicate flood.
- A short report written to `work/` with counts.

## Out of scope

- Real model calls.
- Long-running soak tests.

## Acceptance

- [ ] The run finishes in under five minutes with fake inference.
- [ ] Each invariant has a counter proving it was exercised.
- [ ] A deliberately loosened quota makes the run fail.

## Security

The harness runs the same sandbox and tool profile as production; it does not relax containment for speed.

## Test

The dry run is the test; it also runs in CI on a reduced clock.
