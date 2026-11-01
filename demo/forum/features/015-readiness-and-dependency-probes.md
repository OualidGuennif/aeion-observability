---
id: 015
title: "Readiness and dependency probes"
area: foundation
size: S
parallel: false
depends_on: [002]
owner: builder
status: proposed
---

# 015 — Readiness and dependency probes

**Goal.** Separate liveness from readiness and check the database and collector without exposing versions or secrets, so a deployer knows when to route traffic.

## Scope

- `/readyz` checking a `SELECT 1`, the migration version and a collector reachability probe with a short timeout.
- A 503 answer listing only failed dependency names.
- Cached results for five seconds to avoid a probe storm.

## Out of scope

- Metrics exposition or a status page.
- Any detail about the host.

## Acceptance

- [ ] With the database stopped, `/healthz` stays 200 and `/readyz` answers 503.
- [ ] The answer names the failing dependency once and never repeats a payload.
- [ ] A probe burst does not multiply the database round trips.

## Security

No version string, no connection string, no hostname in the answer.

## Test

Stop the database, assert the split; restart and assert readiness returns.
