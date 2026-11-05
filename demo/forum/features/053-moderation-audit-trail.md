---
id: 053
sequence: 54
title: "Moderation audit trail"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [009, 046, 047, 048, 051]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 053 — Moderation audit trail

## Intent

Route every moderation action through the hash-chained log with a stable action code, so the history of a post can be reconstructed and verified.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Route each existing moderation command to its fixed audit code.
2. Add authorized per-target history and a chain-verification job.
3. Test rollback/concurrent order and absence of content in audit records.

**Scope:**

- Action codes covering hold, approve, reject, lock, sanction, appeal and override.
- A per-target history view for moderators.
- A verifier run in the nightly check.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The application can invoke only the append-only audit function; it has no direct INSERT, UPDATE or DELETE grant on audit history. The separate verifier has restricted read access.

This invariant and the acceptance cases belong to planned protected check `agora-053`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A post held then restored shows exactly two entries in order.
- [ ] The chain verifies after a restart.
- [ ] No entry contains body text.

**Test scenario:** Apply concurrent moderation actions and rollback fixtures, then verify one chain, transaction coupling, order and absence of text.

## Out of scope

- Exporting the trail to a third party.
- Storing post text in the trail.
