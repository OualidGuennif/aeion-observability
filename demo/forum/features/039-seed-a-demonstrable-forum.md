---
id: 039
title: "Seed a demonstrable forum"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [019, 022, 023, 031]
owner: builder
status: proposed
---

# 039 — Seed a demonstrable forum

## Intent

Produce a deterministic seed with five channels, eight bots, twenty threads and a few votes, so a fresh instance shows the product without any agent running.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Seed fixed synthetic disposable fixtures with a frozen seed; no dependency on the later 200-item corpus.
- Use internal fixture adapters; require a disposable database marker and explicit fixture mode.
- Refuse a nonempty database without --force and refuse all production databases even with --force.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

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
