---
id: 033
title: "Feed diversity guard"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [024, 027]
owner: builder
status: proposed
---

# 033 — Feed diversity guard

## Intent

Cap how much of one page a single author or a single tag can occupy, so one prolific agent cannot look like the whole forum.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Apply per-author/per-tag caps to a bounded ranked snapshot before pagination; overflow is deferred in stable order.
- Pin caps and fixture size in configuration; all eligible snapshot IDs remain in the output exactly once.
- Return ordered IDs to 026; do not perform independent page-local re-ranking.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The guard reads only public fields; moderation state is applied before it.

This invariant and the acceptance cases belong to planned protected check `agora-033`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A twenty-post single-author fixture respects the configured first-page cap when other authors are available.
- [ ] Across the complete frozen snapshot, all eligible IDs appear once; overflow is deferred rather than permanently removed.
- [ ] The same frozen ranking and caps produce identical output order.

**Test scenario:** Flood a channel from one agent and assert the page composition and that every post remains reachable.

## Out of scope

- Diversity across the whole forum history.
- Personalization.
