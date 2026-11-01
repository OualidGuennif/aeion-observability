---
id: 016
title: "Graceful shutdown"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 016 — Graceful shutdown

## Intent

Drain in-flight requests and close the pool on SIGTERM within a bounded time, so a deploy never cuts a write in half.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- A signal handler that stops accepting, waits for in-flight work and closes the pool.
- A configurable deadline after which the process exits anyway.
- A log line per phase with a duration.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Shutdown logs carry durations and counts, never request content.

This invariant and the acceptance cases belong to planned protected check `agora-016`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An in-flight request completing before the configured drain deadline finishes after SIGTERM.
- [ ] A new request after shutdown starts is refused without entering its handler.
- [ ] A handler exceeding the deadline is terminated within the configured grace bound; incomplete work is not reported successful.

**Test scenario:** Start a slow request, send SIGTERM and assert the response completes and the exit code is 0.

## Out of scope

- Zero-downtime blue-green orchestration.
- Job draining beyond HTTP requests.
