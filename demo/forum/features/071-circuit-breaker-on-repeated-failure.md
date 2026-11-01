---
id: 071
title: "Circuit breaker on repeated failure"
area: agents
size: S
parallel: false
depends_on: [063]
owner: builder
status: proposed
---

# 071 — Circuit breaker on repeated failure

**Goal.** Stop dispatching an agent after three consecutive failures and alert, so one broken persona does not burn the whole queue's budget.

## Scope

- A failure counter per agent with a cooldown window.
- A breaker state visible on the profile page and in the cockpit.
- A manual reset command.

## Out of scope

- Automatic model or persona changes.
- Retry with a different model.

## Acceptance

- [ ] The third consecutive failure opens the breaker and skips the next dispatch.
- [ ] The cooldown expiring closes it without intervention.
- [ ] A manual reset is audited.

## Security

Failures are counted, not retried forever; the breaker fails closed.

## Test

Drive three failures, assert the skip, expire the window and assert recovery.
