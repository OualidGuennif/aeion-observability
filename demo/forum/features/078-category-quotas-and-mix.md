---
id: 078
sequence: 80
title: "Category quotas and mix"
area: corpus
size: S
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [076]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 078 — Category quotas and mix

## Intent

Fix the share of each category in a day's seeding — a third each, within tolerance — so one category cannot dominate the forum.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Define daily category target/tolerance and seeded tie-breaking.
2. Count committed selections atomically by stable key.
3. Test full/degraded/empty coverage, replay and Europe/Paris day boundaries.

**Scope:**

- Pin one-third daily share per category with five percentage-point tolerance in a frozen 300-selection simulation.
- Choose category before item using transactional counters and seeded tie-breaks; a committed selection counts once per stable selection key.
- Reset on Europe/Paris business days with explicit DST fixtures. Empty categories redistribute with degraded coverage; empty-all refuses dispatch.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The picker reads only category counters and ids.

This invariant and the acceptance cases belong to planned protected check `agora-078`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A day with all categories available lands within the tolerance of a third each.
- [ ] An empty category is compensated by the others, not left as a gap.
- [ ] The counters reset at midnight.

**Test scenario:** Simulate a day with three and with two populated categories; assert the mixes.

## Out of scope

- Personalized category mixes.
- Trend detection.
