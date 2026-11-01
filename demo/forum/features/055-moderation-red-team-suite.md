---
id: 055
title: "Moderation red-team suite"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [042]
owner: builder
status: proposed
---

# 055 — Moderation red-team suite

## Intent

Keep a growing set of bypass attempts — homoglyphs, zero-width characters, encoded payloads, quote tricks — each pinned to the rule that must still catch it.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A fixture of at least forty bypass attempts with the expected verdict.
- A test that fails when a payload passes unflagged.
- A short note per case describing the trick.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The suite is the regression net for the engine; it is never skipped in CI.

This invariant and the acceptance cases belong to planned protected check `agora-055`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every case has a verdict and a rule code.
- [ ] A newly added bypass that passes makes the suite red.
- [ ] The suite runs in under thirty seconds.

**Test scenario:** The suite itself, plus a deliberately weakened engine to prove it fails.

## Out of scope

- Fuzzing in CI.
- Claims of complete coverage.
