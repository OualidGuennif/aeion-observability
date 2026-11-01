---
id: 017
title: "Strict request validation"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 017 — Strict request validation

## Intent

Reject unknown fields, wrong types and oversized bodies at the edge, so no handler ever receives a shape it did not declare.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- Typed request models with `extra=forbid` and bounded strings.
- A body-size limit enforced before parsing.
- A 422 answer listing field paths only.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The limit applies to every route, including the agent API, before authentication work.

This invariant and the acceptance cases belong to planned protected check `agora-017`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An extra field returns 422 before the handler runs.
- [ ] A body exceeding 16384 bytes returns 413 after reading at most the cap plus one byte; parsing/allocation remain bounded.
- [ ] A missing required field names only its path, without its value.

**Test scenario:** Send an extra field, an oversized body and a missing field to a sample route and assert each answer.

## Out of scope

- Content negotiation or versioned request formats.
- Custom coercion rules.
