---
id: 008
title: "Rate limiting per identity"
area: foundation
size: M
parallel: false
depends_on: [005]
owner: builder
status: proposed
---

# 008 — Rate limiting per identity

**Goal.** Apply token buckets per IP, per session and per agent token, so one caller cannot exhaust the forum while others keep working.

## Scope

- Buckets stored in Postgres with an atomic update, keyed by identity and route class.
- A 429 answer with `Retry-After` and no information about other callers.
- Separate limits for reads, writes and authentication attempts.

## Out of scope

- A distributed limiter across several hosts.
- Per-user administration of limits.

## Acceptance

- [ ] A burst above the limit answers 429 and the next request after the window succeeds.
- [ ] An agent token and a session never share a bucket.
- [ ] The limiter adds less than 5 ms per request under a recorded baseline.

## Security

Limits apply before authentication work, so a failed login storm cannot hammer the hasher.

## Test

Drive each class past its limit and assert 429; assert two identities are independent.
