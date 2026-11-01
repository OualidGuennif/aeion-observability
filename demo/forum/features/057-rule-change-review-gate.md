---
id: 057
title: "Rule change review gate"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [041, 009]
owner: builder
status: proposed
---

# 057 — Rule change review gate

## Intent

Make a rule change a reviewed commit with a fixture diff, so a rule cannot be loosened to let a specific post through.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A check that the rules file changed together with a test or a fixture diff.
- A rendered diff of the public rules page in the pull request body.
- A refusal to ship a code removal that old posts cite.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

A fixture diff is necessary but not approval. Rules changes always require owner review and protected checks; candidate-controlled tests cannot certify their own change.

This invariant and the acceptance cases belong to planned protected check `agora-057`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A rules change without a fixture or test change fails the check.
- [ ] The pull request body shows the rendered diff.
- [ ] Removing a cited code is refused.

**Test scenario:** Change the rules alone and assert failure; change with a fixture and assert pass.

## Out of scope

- Approval workflows inside the app.
- Versioned rule branches.
