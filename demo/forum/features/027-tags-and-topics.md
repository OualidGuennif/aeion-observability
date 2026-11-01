---
id: 027
title: "Tags and topics"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 020]
owner: builder
status: proposed
---

# 027 — Tags and topics

## Intent

Attach a small set of controlled tags to posts, so threads can be grouped by topic without free-form taxonomy drift.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- A `tags` table seeded from a fixed list and a join table to posts.
- At most three tags per post, chosen from the list only.
- Tag pages listing posts with the tag.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Tag names are rendered escaped and never used as raw CSS classes.

This invariant and the acceptance cases belong to planned protected check `agora-027`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
