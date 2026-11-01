---
id: 015
title: "Readiness and dependency probes"
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

# 015 — Readiness and dependency probes

## Intent

Separate liveness from readiness and check the database and collector without exposing versions or secrets, so a deployer knows when to route traffic.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- GET /readyz checks database SELECT 1 and migration compatibility with bounded timeouts.
- Database/schema failures return 503 naming failed dependencies only; collector failure is a degraded telemetry flag and does not make the application unready.
- Cache probe results for five seconds.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

No version string, no connection string, no hostname in the answer.

This invariant and the acceptance cases belong to planned protected check `agora-015`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
