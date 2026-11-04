---
id: 038
sequence: 33
title: "Thread subscriptions and digest"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [028, 005, 006]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 038 — Thread subscriptions and digest

## Intent

Offer a bounded per-thread digest and session-protected subscriptions, separate from individual notification records.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add reader subscriptions and a bounded per-thread aggregate view.
2. Protect idempotent unsubscribe with the current session and CSRF.
3. Test capped/hidden digest entries and refusal of state-changing GET.

**Scope:**

- Subscriptions and one bounded digest view per subscribed thread.
- A count of omitted authorized items when the digest cap is exceeded.
- Unsubscribe is a CSRF-protected POST using the existing reader session; GET never changes subscription state.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Subscription mutation requires the authenticated reader session and its CSRF token. The subscription identity is resolved server-side; no bearer unsubscribe token or state-changing GET is introduced.

This invariant and the acceptance cases belong to planned protected check `agora-038`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Ten authorized comments produce one digest view with the expected aggregate; ordinary notification records remain a separate feature.
- [ ] A capped digest reports the omitted count without leaking inaccessible comments.
- [ ] Unsubscribe POST is idempotent; GET or wrong CSRF cannot unsubscribe.

**Test scenario:** Use disposable subscribed-reader fixtures and internal comment fixtures; assert bounded digest counts, visibility filtering and idempotent CSRF-protected unsubscribe POST; GET cannot mutate.

## Out of scope

- Scheduled email delivery.
- Digests across several threads.
