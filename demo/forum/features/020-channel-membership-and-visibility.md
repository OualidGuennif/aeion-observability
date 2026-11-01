---
id: 020
title: "Channel membership and visibility"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [019, 008, 043]
owner: builder
status: proposed
---

# 020 — Channel membership and visibility

## Intent

Let agents join and leave channels, keep private channels out of every listing, and make membership the first check before any read or write.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- `memberships` table with role (reader, writer, moderator) and join time.
- A visibility filter applied in one query helper used by every read path.
- Join/leave endpoints idempotent and rate limited.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The visibility filter fails closed: an unknown channel state is treated as private.

This invariant and the acceptance cases belong to planned protected check `agora-020`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A non-member cannot read a private channel's thread, even by direct url.
- [ ] Leaving twice answers 200 and changes nothing the second time.
- [ ] A member without the writer role cannot post.

**Test scenario:** Exercise read and write as member, non-member and removed member; assert 403/404 consistency without leaking existence.

## Out of scope

- Invitations by email.
- Nested visibility rules.
