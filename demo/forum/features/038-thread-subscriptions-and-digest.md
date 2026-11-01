---
id: 038
title: "Thread subscriptions and digest"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [028, 005, 006]
owner: builder
status: proposed
---

# 038 — Thread subscriptions and digest

## Intent

Offer a bounded per-thread digest and session-protected subscriptions, separate from individual notification records.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Subscriptions and one bounded digest view per subscribed thread.
- A count of omitted authorized items when the digest cap is exceeded.
- Unsubscribe is a CSRF-protected POST using the existing reader session; GET never changes subscription state.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The unsubscribe link carries a signed token scoped to one subscription and one identity.

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
