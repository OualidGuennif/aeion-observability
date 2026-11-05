---
id: 027
sequence: 26
title: "Tags and topics"
area: forum
size: S
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

# 027 — Tags and topics

## Intent

Attach a small set of controlled tags to posts, so threads can be grouped by topic without free-form taxonomy drift.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add the fixed tag list and bounded post-tag relation.
2. Expose authorized React tag pages using existing post reads.
3. Test unknown tags, the three-tag cap and private-channel filtering.

**Scope:**

- A `tags` table seeded from a fixed list and a join table to posts.
- At most three tags per post, chosen from the list only.
- Tag pages listing posts with the tag.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Tag names are rendered escaped and never used as raw CSS classes.

This invariant and the acceptance cases belong to planned protected check `agora-027`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An unknown tag is refused, not created.
- [ ] A fourth tag answers 422.
- [ ] A tag page lists only posts the reader may see.

**Test scenario:** Create posts with zero, three and four tags; assert acceptance, the cap and the visibility filter.

## Out of scope

- User-created tags.
- Tag hierarchies.
