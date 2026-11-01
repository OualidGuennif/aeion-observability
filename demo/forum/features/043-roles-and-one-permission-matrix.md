---
id: 043
title: "Roles and one permission matrix"
area: moderation
size: M
parallel: false
depends_on: [004]
owner: builder
status: proposed
---

# 043 — Roles and one permission matrix

**Goal.** Express every privileged capability as a cell of one matrix enforced in one place, so a new route cannot invent its own authorization.

## Scope

- Roles: reader, writer, moderator, administrator, orchestrator.
- A single `can(role, action)` function with an explicit table and a default of deny.
- A test per cell, positive and negative.

## Out of scope

- Per-object grants.
- A policy language.

## Acceptance

- [ ] Every route declares an action checked by the matrix.
- [ ] A role absent from the table is denied everything.
- [ ] Adding a route without an action fails a startup check.

## Security

Deny by default; an error in the matrix denies rather than allows.

## Test

Walk the matrix in both directions; start the app with a route missing its action and assert the failure.
