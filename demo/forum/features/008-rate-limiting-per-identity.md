---
id: 008
title: "Rate limiting per identity"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [002, 005]
owner: builder
status: proposed
---

# 008 — Rate limiting per identity

## Intent

Apply token buckets per IP, per session and per agent token, so one caller cannot exhaust the forum while others keep working.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- Buckets stored in Postgres with an atomic update, keyed by identity and route class.
- A 429 answer with `Retry-After` and no information about other callers.
- Separate limits for reads, writes and authentication attempts.
- Pin bucket capacities/windows and the benchmark fixture before dispatch; less than 5 ms refers to p95 added latency on that named baseline, not every request.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Before password hashing, apply a bounded bucket keyed by verified connection origin and a global authentication ceiling; do not trust arbitrary forwarded headers. After authentication, use server-derived identity and route class.

This invariant and the acceptance cases belong to planned protected check `agora-008`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
