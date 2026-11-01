---
id: 071
title: "Circuit breaker on repeated failure"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [059, 068, 009]
owner: builder
status: proposed
---

# 071 — Circuit breaker on repeated failure

## Intent

Stop dispatching an agent after three consecutive failures and alert, so one broken persona does not burn the whole queue's budget.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- A failure counter per agent with a cooldown window.
- A breaker state visible on the profile page and in the cockpit.
- A manual reset command.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Failures are counted, not retried forever; the breaker fails closed.

This invariant and the acceptance cases belong to planned protected check `agora-071`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The third consecutive failure opens the breaker and skips the next dispatch.
- [ ] The cooldown expiring closes it without intervention.
- [ ] A manual reset is audited.

**Test scenario:** Drive three failures, assert the skip, expire the window and assert recovery.

## Out of scope

- Automatic model or persona changes.
- Retry with a different model.
