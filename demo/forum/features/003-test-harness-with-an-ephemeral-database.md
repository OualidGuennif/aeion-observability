---
id: 003
sequence: 3
title: "Test harness with an ephemeral database"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [002]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 003 — Test harness with an ephemeral database

## Intent

Run Quarkus/JUnit suites against independent disposable PostgreSQL databases and a frozen clock, with no dependency on developer or production data.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Create the owned disposable PostgreSQL test resource and clock injection.
2. Isolate transaction tests and HTTP tests using their actual transaction boundaries.
3. Run concurrent suites and prove cleanup plus refusal before unsafe DDL.

**Scope:**

- A JUnit/Quarkus test resource creates a uniquely named disposable PostgreSQL database, applies the real migrations and cleans up only that owned database.
- Independent tests use transaction rollback where valid; HTTP/async tests with separate transactions use isolated fixtures and explicit cleanup instead of assuming a client rollback covers the server.
- Inject a frozen Java clock and seeded random source. Refuse unmarked databases and unapproved hosts before any DDL.
- The protected factory supplies its own immutable harness outside candidate control; builders may add product tests but cannot weaken the acceptance runner.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Use dedicated disposable PostgreSQL credentials, a generated allowlisted database name and no production connection settings. Logs contain only fixed failure codes and opaque test identity.

This invariant and the acceptance cases belong to planned protected check `agora-003`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two suites run at once without interfering.
- [ ] A test that leaves a row does not change the next test's result.
- [ ] Pointing the harness at a database without the disposable marker aborts before any DDL.

**Test scenario:** Run two Quarkus/JUnit suites concurrently against separate disposable PostgreSQL databases; verify rollback and HTTP cleanup, refusal before DDL and cleanup after interrupted tests.

## Out of scope

- Browser automation or load testing.
- A test dashboard.
