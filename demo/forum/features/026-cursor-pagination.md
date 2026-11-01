---
id: 026
title: "Cursor pagination"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 026 — Cursor pagination

**Goal.** Page every listing with an opaque cursor instead of an offset, so new posts never shift a reader's position and a page size is always bounded.

## Scope

- A cursor encoding the last sort key and id, signed to prevent tampering.
- A helper every listing uses, with a maximum page size.
- A 400 answer for a malformed or forged cursor.

## Out of scope

- Offset pagination or total counts.
- Infinite scroll.

## Acceptance

- [ ] Inserting a post between page one and two does not duplicate or skip an item.
- [ ] A forged cursor answers 400 without a stack trace.
- [ ] Requesting a page size above the cap returns the cap.

## Security

The cursor is signed; a tampered value is refused rather than coerced.

## Test

Page a fixture while inserting rows; assert no duplicates or gaps, and assert the forged-cursor refusal.
