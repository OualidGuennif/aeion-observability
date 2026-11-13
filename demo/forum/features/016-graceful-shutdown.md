---
id: 016
sequence: 16
title: "Graceful shutdown"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [001, 002]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 016 — Graceful shutdown

## Intent

Drain in-flight requests and close the pool on SIGTERM within a bounded time, so a deploy never cuts a write in half.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Configure Quarkus draining and JDBC lifecycle cleanup.
2. Set a bounded grace deadline and fixed shutdown phase events.
3. Test completion before the deadline and honest termination after it.

**Scope:**

- Use Quarkus graceful shutdown configuration and lifecycle hooks rather than installing a second independent signal handler.
- Stop admission, drain bounded in-flight requests and close the JDBC pool under a configured deadline.
- Log fixed phase codes, durations and counts; transactional writes are either committed or rolled back, never claimed successful after forced termination.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Shutdown logs carry durations and counts, never request content.

This invariant and the acceptance cases belong to planned protected check `agora-016`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An in-flight request completing before the configured drain deadline finishes after SIGTERM.
- [ ] A new request after shutdown starts is refused without entering its handler.
- [ ] A handler exceeding the deadline is terminated within the configured grace bound; incomplete work is not reported successful.

**Test scenario:** Start a slow request in JUnit/integration lifecycle tests, send SIGTERM and assert the response completes and exit code is 0 (external black-box HTTP tests never signal the server).

## Out of scope

- Zero-downtime blue-green orchestration.
- Job draining beyond HTTP requests.
