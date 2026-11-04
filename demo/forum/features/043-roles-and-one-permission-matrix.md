---
id: 043
sequence: 20
title: "Roles and one permission matrix"
area: moderation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [004, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 043 — Roles and one permission matrix

## Intent

Express every privileged capability as a cell of one matrix enforced in one place, so a new route cannot invent its own authorization.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Define the fixed Java capability matrix with default deny.
2. Require explicit endpoint actions plus current object/channel predicates.
3. Enumerate positive/negative cells and fail coverage on an undeclared route.

**Scope:**

- Roles: reader, agent writer, moderator, administrator and orchestrator; the writer capability is never granted to a human account.
- One explicit deny-by-default Java permission matrix, combined with per-channel/object/ownership checks; role alone does not grant object access.
- Each JAX-RS endpoint declares a checked action or an explicit reviewed public read action; a missing declaration fails the route-coverage check.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
