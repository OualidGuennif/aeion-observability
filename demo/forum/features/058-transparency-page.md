---
id: 058
title: "Transparency page"
area: moderation
size: S
parallel: false
depends_on: [053]
owner: builder
status: proposed
---

# 058 — Transparency page

**Goal.** Publish aggregate moderation counts — held, rejected, restored, appeals upheld — from the audit trail, so the forum's own behaviour is visible without exposing content.

## Scope

- A public page with counts per week and per rule code, computed from the audit table.
- A minimum cohort size below which a count is bucketed to avoid identification.
- A cached render with the timestamp of the last computation.

## Out of scope

- Per-post histories in public.
- Naming moderators.

## Acceptance

- [ ] Counts match a recomputation from the trail.
- [ ] Small cohorts are bucketed, not printed.
- [ ] The page never mentions a handle or a post id.

## Security

Aggregation happens in SQL over codes and timestamps only; no content column is read.

## Test

Compute twice and assert equality with the raw query; assert bucketing under the threshold.
