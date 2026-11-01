---
id: 070
title: "Thread summaries in Hindsight"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [069, 022]
owner: builder
status: proposed
---

# 070 — Thread summaries in Hindsight

## Intent

Retain one deterministic public-thread category/count/outcome summary in Hindsight, with stable identity, deletion and retention; no body analysis or model call is needed.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- On thread closure, a trusted background operation creates one deterministic summary of public category/count/outcome metadata, without reading bodies.
- Store a stable thread/version key, bounded codes/counts and a retention deadline in the demo synthetic namespace.
- Delete or update records idempotently when public visibility changes; private thread content/identity is never retained.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Summaries are generated from public text only and stored in the demo's synthetic namespace.

This invariant and the acceptance cases belong to planned protected check `agora-070`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Repeated close notifications retain one record per public thread/version.
- [ ] The record has only allowlisted codes/counts/opaque IDs, no handles or body excerpts of any length.
- [ ] Deletion or loss of visibility removes the corresponding record by the next bounded background run.

**Test scenario:** Deliver repeated close/delete/visibility events; assert idempotent records, exact metadata schema, retention and removal without body/handle fields.

## Out of scope

- Semantic search in the product UI.
- Summarizing held content.
