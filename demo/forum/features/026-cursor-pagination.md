---
id: 026
sequence: 38
title: "Cursor pagination"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [021, 024, 033, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 026 — Cursor pagination

## Intent

Paginate a bounded frozen ordered snapshot with reader-bound signed cursors, explicit expiry and current visibility checks; later posts enter a new snapshot.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Freeze a bounded ordered snapshot after ranking and diversity.
2. Issue reader-bound signed cursors and recheck visibility per page.
3. Test inserts, expiry, forged/wrong-reader cursors and membership removal.

**Scope:**

- Create a bounded ordered snapshot of at most 1000 eligible post IDs after ranking/diversity, with a five-minute expiry and server-derived reader identity.
- Use a signed cursor for snapshot ID and position; every page rechecks current visibility, and newly hidden rows are explicitly omitted.
- Refuse forged, expired or wrong-reader cursors; page size is at most 50.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
