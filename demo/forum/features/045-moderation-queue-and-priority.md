---
id: 045
title: "Moderation queue and priority"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [044, 041, 043]
owner: builder
status: proposed
---

# 045 — Moderation queue and priority

## Intent

Order the queue by rule severity, report count and age with a stable tie-break, so the worst content is seen first and nothing starves.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A queue query computing a priority from severity, distinct reporters and age.
- A starvation guard that lifts old items after a documented threshold.
- A view showing the components behind each item's position.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The queue is visible only to moderators; its query is covered by the permission matrix.

This invariant and the acceptance cases belong to planned protected check `agora-045`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A high-severity item outranks a low-severity one filed earlier.
- [ ] An old low-severity item eventually outranks a fresh one.
- [ ] Two items with equal components order by id, stably.

**Test scenario:** Build a fixture with mixed severities and ages; assert the order and the starvation lift.

## Out of scope

- Assignment to individual moderators.
- SLA timers or escalation by clock.
