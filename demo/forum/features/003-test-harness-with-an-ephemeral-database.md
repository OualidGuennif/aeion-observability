---
id: 003
title: "Test harness with an ephemeral database"
area: foundation
size: S
parallel: false
depends_on: [002]
owner: builder
status: proposed
---

# 003 — Test harness with an ephemeral database

**Goal.** Give every test an isolated database and a deterministic clock, so the suites can run in parallel and never touch a developer's data.

## Scope

- A pytest fixture that creates a database, applies migrations once per session and rolls back per test.
- A frozen clock and a seeded random source.
- A refusal to run when the target database name is not marked as disposable.

## Out of scope

- Browser automation or load testing.
- A test dashboard.

## Acceptance

- [ ] Two suites run at once without interfering.
- [ ] A test that leaves a row does not change the next test's result.
- [ ] Pointing the harness at a database without the disposable marker aborts before any DDL.

## Security

The fixture refuses production-looking hosts and prints only the database name.

## Test

Run the suite twice in parallel and assert identical results; assert the marker check blocks a named database.
