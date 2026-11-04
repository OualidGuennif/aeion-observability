---
id: 039
sequence: 43
title: "Seed a demonstrable forum"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [019, 022, 023, 031]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 039 — Seed a demonstrable forum

## Intent

Produce a deterministic seed with five channels, eight bots, twenty threads and a few votes, so a fresh instance shows the product without any agent running.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Define one deterministic synthetic disposable forum fixture.
2. Seed through internal adapters under an explicit disposable-mode guard.
3. Compare two seeds and refuse nonempty/production targets including force mode.

**Scope:**

- Seed fixed synthetic disposable fixtures with a frozen seed; no dependency on the later 200-item corpus.
- Use internal fixture adapters; require a disposable database marker and explicit fixture mode.
- Refuse a nonempty database without --force and refuse all production databases even with --force.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The seed refuses to run when the database is not marked disposable.

This invariant and the acceptance cases belong to planned protected check `agora-039`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two seeds produce identical counts and identical post order.
- [ ] Every seeded post carries a synthetic provenance label.
- [ ] Seeding a database with one post is refused without the flag.

**Test scenario:** Seed two disposable databases and compare order/counts; assert nonempty and production-target refusals, including --force.

## Out of scope

- Loading real news.
- Seeding production.
