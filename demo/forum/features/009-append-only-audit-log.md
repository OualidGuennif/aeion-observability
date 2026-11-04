---
id: 009
sequence: 9
title: "Append-only audit log"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [002]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 009 — Append-only audit log

## Intent

Record privileged actions in a serialized hash-chained PostgreSQL audit log with a restricted verifier, so accidental or unauthorized history mutation is detectable.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Define audit codes, canonical hash input and the append-only SQL function.
2. Couple action and audit transactions with serialized predecessor allocation.
3. Test concurrent appends, rollback, tampering and database grant refusals.

**Scope:**

- An audit table stores sequence, actor, fixed action code, target identity, outcome, previous hash and entry hash; no body text or justification text.
- An append-only database function serializes the predecessor under a transaction lock and appends within the same transaction as the privileged mutation. The application has EXECUTE on that function, no direct audit DML.
- A separately authorized verifier reads the chain and reports the first break; security-definer functions pin their search path and do not accept dynamic SQL.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Application roles cannot update/delete audit rows or replace the append function. A separate restricted verifier may SELECT. Hash chaining alone cannot detect a privileged administrator rewriting the whole chain; an external anchor would be a separately reviewed capability.

This invariant and the acceptance cases belong to planned protected check `agora-009`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Editing one row makes `verify` fail at that sequence.
- [ ] A failed action is audited with its outcome, not dropped.
- [ ] The chain survives a restart.

**Test scenario:** Run concurrent appends and action rollbacks; assert one verifiable chain with no fork, committed outcomes, restart survival, and UPDATE/DELETE denial. Tamper only through a disposable test administrator.

## Out of scope

- Log shipping to a third party.
- Content capture: audit records codes and identifiers, not text.
