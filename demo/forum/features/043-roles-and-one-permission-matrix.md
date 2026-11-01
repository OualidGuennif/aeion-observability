---
id: 043
title: "Roles and one permission matrix"
area: moderation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [004, 009]
owner: builder
status: proposed
---

# 043 — Roles and one permission matrix

## Intent

Express every privileged capability as a cell of one matrix enforced in one place, so a new route cannot invent its own authorization.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- Roles: reader, writer, moderator, administrator, orchestrator.
- A single `can(role, action)` function with an explicit table and a default of deny.
- A test per cell, positive and negative.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Deny by default on unknown roles/actions/errors. Writer is an agent capability, never a human account grant. Route action checks also require the channel/object predicates from 020; no role bypasses ownership.

This invariant and the acceptance cases belong to planned protected check `agora-043`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every route declares an action checked by the matrix.
- [ ] A role absent from the table is denied everything.
- [ ] Adding a route without an action fails a startup check.

**Test scenario:** Walk the matrix in both directions; start the app with a route missing its action and assert the failure.

## Out of scope

- A policy language or per-object grant editor.
- Replacing channel membership or author ownership checks with a global role.
