---
id: 042
title: "Deterministic rules engine"
area: moderation
size: L
parallel: false
depends_on: [041]
owner: builder
status: proposed
---

# 042 — Deterministic rules engine

**Goal.** Decide hold, reject or allow from the content and the rule set alone, with no model in the decision path, so the same input always yields the same verdict and reason code.

## Scope

- A pipeline of checks: length, links, caps, banned terms, duplicate score, rate signals.
- A verdict object carrying decision, rule code, severity and the evidence fields it used.
- A pure function with no I/O, so it is table-testable.

## Out of scope

- Semantic understanding or toxicity scoring by a model.
- Automatic bans from the engine.

## Acceptance

- [ ] The same content and rules yield byte-identical verdicts across runs.
- [ ] Every verdict names exactly one primary rule code.
- [ ] An unknown input shape is rejected, not treated as allowed.

## Security

Fail closed: a check that errors produces a hold, never an allow.

## Test

A table of at least forty inputs with expected verdicts and codes, including the failing-check path.
