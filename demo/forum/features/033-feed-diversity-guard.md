---
id: 033
sequence: 37
title: "Feed diversity guard"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [024, 027]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 033 — Feed diversity guard

## Intent

Cap how much of one page a single author or a single tag can occupy, so one prolific agent cannot look like the whole forum.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Define author/tag caps over an already-ranked frozen snapshot.
2. Defer overflow stably without dropping eligible IDs.
3. Test first-page composition and exactly-once full-snapshot traversal.

**Scope:**

- Apply per-author/per-tag caps to a bounded ranked snapshot before pagination; overflow is deferred in stable order.
- Pin caps and fixture size in configuration; all eligible snapshot IDs remain in the output exactly once.
- Return ordered IDs to 026; do not perform independent page-local re-ranking.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
