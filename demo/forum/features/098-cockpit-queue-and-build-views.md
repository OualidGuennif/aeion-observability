---
id: 098
title: "Cockpit queue and build views"
area: cockpit
size: M
parallel: true
depends_on: [089]
owner: builder
status: proposed
---

# 098 — Cockpit queue and build views

**Goal.** Add the two pages the owner asked for: the 100 features with one Build button each, and one build page streaming what the agent is doing.

## Scope

- A features page with area groups, dependency hints and enqueue controls.
- A build page with the spec, the step timeline, the checks and the pull request link.
- Server-sent events for the live view, falling back to a refresh without JavaScript.

## Out of scope

- A JavaScript framework or a client build step.
- Multi-user realtime collaboration.

## Acceptance

- [ ] Clicking Build on a feature enqueues exactly that id and shows it.
- [ ] The build page updates within two seconds of a new step.
- [ ] With JavaScript off, the page still shows the current state on reload.

## Security

The cockpit stays on loopback and requires the administrator session; every action carries the CSRF token.

## Test

Drive the pages with a stub queue, with and without JavaScript.
