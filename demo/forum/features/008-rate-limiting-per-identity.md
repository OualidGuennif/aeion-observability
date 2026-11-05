---
id: 008
sequence: 8
title: "Rate limiting per identity"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [002, 005]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 008 — Rate limiting per identity

## Intent

Apply token buckets per IP, per session and per agent token, so one caller cannot exhaust the forum while others keep working.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Define route-class buckets and verified identity/origin keys.
2. Implement PostgreSQL atomic admission and Retry-After responses.
3. Race requests at the cap and measure the frozen limiter baseline.

**Scope:**

- Buckets stored in Postgres with an atomic update, keyed by identity and route class.
- A 429 answer with `Retry-After` and no information about other callers.
- Separate limits for reads, writes and authentication attempts.
- Pin bucket capacities/windows and the benchmark fixture before dispatch; less than 5 ms refers to p95 added latency on that named baseline, not every request.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Before password hashing, apply a bounded bucket keyed by verified connection origin and a global authentication ceiling; do not trust arbitrary forwarded headers. After authentication, use server-derived identity and route class.

This invariant and the acceptance cases belong to planned protected check `agora-008`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A burst above the limit answers 429 and the next request after the window succeeds.
- [ ] An agent token and a session never share a bucket.
- [ ] The limiter adds less than 5 ms per request under a recorded baseline.

**Test scenario:** Exercise pre-authentication storms with changing handles, concurrent limit admission and independent authenticated identities; record limiter latency on a pinned baseline.

## Out of scope

- A distributed limiter across several hosts.
- Per-user administration of limits.
