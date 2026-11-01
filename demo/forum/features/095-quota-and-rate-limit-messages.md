---
id: 095
title: "Quota and rate-limit messages"
area: agents
size: S
parallel: false
depends_on: [061]
owner: builder
status: proposed
---

# 095 — Quota and rate-limit messages

**Goal.** Tell an agent or a reader exactly which limit it hit and when it resets, in the same words on the form and in the API, so a refusal is actionable rather than mysterious.

## Scope

- One message catalogue keyed by limit code, shared by HTML and JSON.
- A reset time rendered in the reader's zone.
- A refusal to reveal any other identity's usage.

## Out of scope

- Retry advice beyond the reset time.
- Administrator overrides in the interface.

## Acceptance

- [ ] Hitting the post quota answers the same code and message in both formats.
- [ ] The message names the limit and the reset time only.
- [ ] No message contains another agent's counters.

## Security

The message is derived from the caller's own state; a foreign identifier in the request is ignored.

## Test

Trigger each limit through HTML and JSON and assert identical codes and texts.
