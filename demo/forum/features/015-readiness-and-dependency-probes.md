---
id: 015
sequence: 15
title: "Readiness and dependency probes"
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

# 015 — Readiness and dependency probes

## Intent

Separate liveness from readiness and check the database and collector without exposing versions or secrets, so a deployer knows when to route traffic.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Add bounded PostgreSQL/schema readiness separately from liveness.
2. Report collector outage as degraded metadata rather than database failure.
3. Test database stop/recovery and five-second probe coalescing.

**Scope:**

- GET /readyz checks database SELECT 1 and migration compatibility with bounded timeouts.
- Database/schema failures return 503 naming failed dependencies only; collector failure is a degraded telemetry flag and does not make the application unready.
- Cache probe results for five seconds.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

No version string, no connection string, no hostname in the answer.

This invariant and the acceptance cases belong to planned protected check `agora-015`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] With the database stopped, `/healthz` stays 200 and `/readyz` answers 503.
- [ ] The answer names the failing dependency once and never repeats a payload.
- [ ] A probe burst does not multiply the database round trips.

**Test scenario:** Stop the database, assert the split; restart and assert readiness returns.

## Out of scope

- Metrics exposition or a status page.
- Any detail about the host.
