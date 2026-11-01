---
id: 049
title: "Escalation ladder"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [048]
owner: builder
status: proposed
---

# 049 — Escalation ladder

## Intent

Turn repeated upheld violations into warn, then mute, then ban, by a table with documented thresholds rather than a moderator's mood.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A ladder table keyed by upheld violations within a window.
- A single function returning the next sanction for an identity.
- A dry-run mode printing what would happen.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Only upheld decisions count; a dismissed report never escalates.

This invariant and the acceptance cases belong to planned protected check `agora-049`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Three upheld violations in a week produce a mute, not a ban.
- [ ] The ladder resets after the window passes.
- [ ] The dry run matches the real outcome on the same fixture.

**Test scenario:** Simulate violations across the window boundary; assert each rung and the dry-run equality.

## Out of scope

- Machine-learning risk scores.
- Ladder changes without a review.
