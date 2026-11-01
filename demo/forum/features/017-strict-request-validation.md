---
id: 017
title: "Strict request validation"
area: foundation
size: S
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 017 — Strict request validation

**Goal.** Reject unknown fields, wrong types and oversized bodies at the edge, so no handler ever receives a shape it did not declare.

## Scope

- Typed request models with `extra=forbid` and bounded strings.
- A body-size limit enforced before parsing.
- A 422 answer listing field paths only.

## Out of scope

- Content negotiation or versioned request formats.
- Custom coercion rules.

## Acceptance

- [ ] An extra field answers 422 and the handler is never called.
- [ ] A body above the limit answers 413 without being read into memory.
- [ ] A missing required field names the field path.

## Security

The limit applies to every route, including the agent API, before authentication work.

## Test

Send an extra field, an oversized body and a missing field to a sample route and assert each answer.
