---
id: 075
title: "Corpus item schema"
area: corpus
size: S
parallel: false
depends_on: [002]
owner: builder
status: proposed
---

# 075 — Corpus item schema

**Goal.** Define one news item — synthetic title, category, date, short excerpt, source label — with a stable id, so every later corpus feature shares one shape.

## Scope

- A schema with id, category (tech, state, government), title, excerpt, date, synthetic flag.
- Length caps and a required `synthetic: true` in this deployment.
- A validator run in tests and at load time.

## Out of scope

- Real sources or attributed quotes.
- Images or media.

## Acceptance

- [ ] An item without the synthetic flag is refused.
- [ ] An unknown category is refused.
- [ ] An excerpt above the cap is rejected, not truncated silently.

## Security

The schema has no field for a URL, so no item can carry a link into the forum.

## Test

Validate a good item and four malformed ones; assert the exact refusals.
