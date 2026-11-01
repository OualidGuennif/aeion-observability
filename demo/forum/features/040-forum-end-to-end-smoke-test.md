---
id: 040
title: "Forum end-to-end smoke test"
area: forum
size: M
parallel: false
depends_on: [039]
owner: builder
status: proposed
---

# 040 — Forum end-to-end smoke test

**Goal.** Drive the whole forum through HTTP on a seeded instance — read, post, reply, vote, flag, moderate — so a regression anywhere in the chain fails one test.

## Scope

- A test that starts the app against an ephemeral database and walks the flows.
- Assertions on status codes, rendered content, audit entries and telemetry spans.
- A refused path for a non-member and for a bot without a persona.

## Out of scope

- Browser-driven visual tests.
- Load or concurrency assertions.

## Acceptance

- [ ] The scenario passes from a clean database in under two minutes.
- [ ] Removing a control from any step makes the scenario fail.
- [ ] The test leaves no state behind.

## Security

The scenario exercises the refusals, not only the happy path.

## Test

The smoke test is the test.
