---
id: 003
title: "Test harness with an ephemeral database"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [002]
owner: builder
status: proposed
---

# 003 — Test harness with an ephemeral database

## Intent

Give every test an isolated database and a deterministic clock, so the suites can run in parallel and never touch a developer's data.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- A pytest fixture that creates a database, applies migrations once per session and rolls back per test.
- A frozen clock and a seeded random source.
- A refusal to run when the target database name is not marked as disposable.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The fixture refuses production-looking hosts and prints only the database name.

This invariant and the acceptance cases belong to planned protected check `agora-003`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two suites run at once without interfering.
- [ ] A test that leaves a row does not change the next test's result.
- [ ] Pointing the harness at a database without the disposable marker aborts before any DDL.

**Test scenario:** Run the suite twice in parallel and assert identical results; assert the marker check blocks a named database.

## Out of scope

- Browser automation or load testing.
- A test dashboard.
