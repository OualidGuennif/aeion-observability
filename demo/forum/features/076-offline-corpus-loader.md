---
id: 076
title: "Offline corpus loader"
area: corpus
size: M
parallel: false
depends_on: [075]
owner: builder
status: proposed
---

# 076 — Offline corpus loader

**Goal.** Load the corpus from a local directory only, with no network client in the process, so the ingestion path cannot reach the internet.

## Scope

- A loader reading JSON files from a configured directory and writing them to Postgres idempotently.
- A checksum per item and a count report.
- A test asserting that no HTTP client is imported by the loader's dependency set.

## Out of scope

- RSS, scrapers or any remote fetch.
- Scheduling through a cloud service.

## Acceptance

- [ ] Loading twice yields the same row count and no duplicates.
- [ ] A malformed file is reported and skipped, never partially applied.
- [ ] The loader runs with outbound network disabled.

## Security

The process has no network route and no fetch dependency; this is asserted, not assumed.

## Test

Load twice, add a malformed file, and run the dependency assertion.
