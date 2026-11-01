---
id: 058
title: "Transparency page"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [053, 014]
owner: builder
status: proposed
---

# 058 — Transparency page

## Intent

Publish aggregate moderation counts — held, rejected, restored, appeals upheld — from the audit trail, so the forum's own behaviour is visible without exposing content.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A public page with counts per week and per rule code, computed from the audit table.
- A minimum cohort size below which a count is bucketed to avoid identification.
- A cached render with the timestamp of the last computation.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Aggregation happens in SQL over codes and timestamps only; no content column is read.

This invariant and the acceptance cases belong to planned protected check `agora-058`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Counts match a recomputation from the trail.
- [ ] Small cohorts are bucketed, not printed.
- [ ] The page never mentions a handle or a post id.

**Test scenario:** Compute twice and assert equality with the raw query; assert bucketing under the threshold.

## Out of scope

- Per-post histories in public.
- Naming moderators.
