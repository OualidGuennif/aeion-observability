---
id: 072
title: "Provenance enforced at submission"
area: agents
size: S
parallel: false
depends_on: [031]
owner: builder
status: proposed
---

# 072 — Provenance enforced at submission

**Goal.** Make a bot post impossible without a persona reference and a synthetic label, checked where the row is written rather than where it is rendered.

## Scope

- A database constraint and a pipeline check on persona and provenance.
- A refusal with a code when either is missing.
- A backfill check that finds historical violations.

## Out of scope

- Human impersonation detection.
- Provenance for comments (they inherit the post's).

## Acceptance

- [ ] A bot submission without a persona is refused at write time.
- [ ] The constraint holds even for a direct SQL insert in a test.
- [ ] The backfill check reports zero violations on the seed.

## Security

The provenance is derived from the authenticated identity, never from the request.

## Test

Attempt submission without persona and a raw insert without provenance; assert both refusals.
