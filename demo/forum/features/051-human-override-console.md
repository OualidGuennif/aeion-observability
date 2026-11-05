---
id: 051
sequence: 52
title: "Human override console"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [046, 005, 006, 009, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 051 — Human override console

## Intent

Let the administrator overturn any moderation action from one page, with a mandatory justification, so a wrong automated decision is one click from repair.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Add the fresh-session administrator React override view.
2. Store bounded private justification separately from fixed-code audit records.
3. Test confirmation/CSRF/rate limits, restoration and non-admin refusals.

**Scope:**

- An administrator React console lists authorized actions with safe bounded evidence and restore controls.
- Require a bounded private justification record linked by opaque ID; the append-only audit stores a fixed override code and that ID, never free text.
- Require fresh authentication, CSRF, an explicit confirmation and a fixed override rate limit; current object/visibility checks remain enforced.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The console requires a fresh session, and every view is audited.

This invariant and the acceptance cases belong to planned protected check `agora-051`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An override restores visibility and appends an audit entry citing the original action.
- [ ] An override without justification is refused.
- [ ] The console is unreachable for non-administrators, including by url.

**Test scenario:** Override a hold, assert restoration and audit; attempt the console as moderator and assert 403.

## Out of scope

- Editing audit rows.
- Overriding the audit chain itself.
