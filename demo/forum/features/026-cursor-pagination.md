---
id: 026
title: "Cursor pagination"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 024, 033, 020]
owner: builder
status: proposed
---

# 026 — Cursor pagination

## Intent

Paginate a bounded frozen ordered snapshot with reader-bound signed cursors, explicit expiry and current visibility checks; later posts enter a new snapshot.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Create a bounded ordered snapshot of at most 1000 eligible post IDs after ranking/diversity, with a five-minute expiry and server-derived reader identity.
- Use a signed cursor for snapshot ID and position; every page rechecks current visibility, and newly hidden rows are explicitly omitted.
- Refuse forged, expired or wrong-reader cursors; page size is at most 50.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The cursor is signed; a tampered value is refused rather than coerced.

This invariant and the acceptance cases belong to planned protected check `agora-026`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] On a fixed visible fixture, pages have no repeated or missing snapshot IDs after a new post is inserted; the new post waits for a new snapshot.
- [ ] Forged and wrong-reader cursors return 400; expired snapshots return 409; no private post is revealed after membership removal.
- [ ] Page-size requests above 50 are capped and a snapshot never stores more than 1000 IDs.

**Test scenario:** Page a fixture while inserting rows; assert no duplicates or gaps, and assert the forged-cursor refusal.

## Out of scope

- Offset pagination or total counts.
- Infinite scroll.
