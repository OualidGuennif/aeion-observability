---
id: 094
title: "French typography and dates"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [014]
owner: builder
status: proposed
---

# 094 — French typography and dates

## Intent

Apply French conventions — non-breaking spaces before punctuation, guillemets, and readable dates — without a localization framework.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- A text filter used by every template for punctuation spacing and quotes.
- Date rendering in French, with relative times for recent posts.
- A test table of typographic cases.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Typography transforms plain text nodes before final escaping, never serialized HTML or attributes; it cannot introduce markup or change an authorization decision.

This invariant and the acceptance cases belong to planned protected check `agora-094`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A colon, semicolon, question or exclamation mark renders after a non-breaking space.
- [ ] Guillemets close correctly around a quoted phrase.
- [ ] Relative times switch to absolute dates after a week.

**Test scenario:** A table of twenty strings, asserted character by character.

## Out of scope

- Other languages.
- A translation workflow.
