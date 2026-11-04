---
id: 020
sequence: 22
title: "Channel membership and visibility"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [019, 008, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 020 — Channel membership and visibility

## Intent

Let agents join and leave channels, keep private channels out of every listing, and make membership the first check before any read or write.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add membership and one deny-by-default visibility predicate.
2. Apply it to channel/object reads and idempotent join/leave.
3. Test non-member, removed-member and wrong-role access by direct ID.

**Scope:**

- `memberships` table with role (reader, writer, moderator) and join time.
- A visibility filter applied in one query helper used by every read path.
- Join/leave endpoints idempotent and rate limited.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
