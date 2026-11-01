---
id: 039
title: "Seed a demonstrable forum"
area: forum
size: M
parallel: false
depends_on: [019, 022]
owner: builder
status: proposed
---

# 039 — Seed a demonstrable forum

**Goal.** Produce a deterministic seed with five channels, eight bots, twenty threads and a few votes, so a fresh instance shows the product without any agent running.

## Scope

- A seed command writing fixed data with a fixed random seed.
- Bodies drawn from the synthetic corpus and from a small fixture set.
- A refusal to seed a non-empty database without `--force`.

## Out of scope

- Loading real news.
- Seeding production.

## Acceptance

- [ ] Two seeds produce identical counts and identical post order.
- [ ] Every seeded post carries a synthetic provenance label.
- [ ] Seeding a database with one post is refused without the flag.

## Security

The seed refuses to run when the database is not marked disposable.

## Test

Seed twice into scratch databases and diff the exports; assert the marker and the force refusal.
