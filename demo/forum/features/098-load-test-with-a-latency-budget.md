---
id: 098
sequence: 98
title: "Load test with a latency budget"
area: ops
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [034, 039, 025, 026]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 098 — Load test with a latency budget

## Intent

Drive fifty concurrent readers against a seeded instance and pin a p95 budget per route, so performance is a number the build can fail on.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Pin the disposable fixture, route mix, resources and latency budgets.
2. Run fifty readers for three measured repetitions after warm-up.
3. Report all percentiles and fail tightened budgets or inconsistent repetitions.

**Scope:**

- Drive fifty concurrent readers with a frozen request mix, 10-second warm-up and 60-second measurement.
- Before qualification record runtime versions, CPU/memory limits, fixture digest and p95 budgets per route in the report contract.
- Run three repetitions; report p50/p95/p99 and compare against fixed budgets with a documented 20 percent cross-run tolerance.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The script targets a disposable instance and refuses a host it does not recognise as local.

This invariant and the acceptance cases belong to planned protected check `agora-098`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The report includes per-route p50/p95/p99, fixture/runtime/hardware identity and all three repetitions.
- [ ] A deliberately tightened budget produces nonzero exit with the route named.
- [ ] A run outside the 20 percent repeatability tolerance is inconclusive/failed, never presented as passing performance evidence.

**Test scenario:** Run against a seeded instance and assert the report shape and the exit code on a tightened budget.

## Out of scope

- Distributed load generation.
- Capacity planning.
