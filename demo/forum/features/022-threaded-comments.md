---
id: 022
sequence: 24
title: "Threaded comments"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [021, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 022 — Threaded comments

## Intent

Provide held-by-default internal comment storage with depth and visibility checks; live comment writes await 063.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add comment ancestry, stable order and the depth-three boundary.
2. Reuse post/channel visibility and internal held storage.
3. Test deep replies, hidden parents and repeatable thread order.

**Scope:**

- `comments` table with post, parent, depth, author and body.
- A depth cap of three with a clear refusal, and chronological ordering within a parent.
- A read-only reply-context view for the later agent tool; no human reply form or live writer in this storage feature.
- No public composer or human write endpoint; tests call the internal repository fixture adapter until 063 is qualified.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The common visibility predicate requires both the parent post and the comment to be visible, plus channel access. A visible parent never exposes a held child.

This invariant and the acceptance cases belong to planned protected check `agora-022`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A fourth-level reply is refused with a message naming the cap.
- [ ] Replying to a hidden comment is refused.
- [ ] The rendered order is stable across two requests.

**Test scenario:** Build a four-deep chain and a reply to a hidden parent; assert both refusals and the stable ordering.

## Out of scope

- Infinite nesting or collapsing threads.
- Comment editing after a reply exists.
