---
id: 054
title: "Moderation KPIs on synthetic labels"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [046]
owner: builder
status: proposed
---

# 054 — Moderation KPIs on synthetic labels

## Intent

Measure deterministic-engine precision/recall on a held-out labelled synthetic fixture; moderator-proposal comparison is optional only after 050 is qualified.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- Two hundred labelled synthetic cases split by stable IDs into 100 tuning and 100 held-out cases.
- Report engine per-code confusion, precision and recall; optional moderator proposal evaluation waits for qualified 050.
- Pin minimum recall 0.95 and precision 0.95 on the held-out synthetic set, with denominators and unknown cases explicit.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The fixture is synthetic and labelled; it is not benchmark evidence about any real community.

This invariant and the acceptance cases belong to planned protected check `agora-054`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The report names the per-code confusion, not only the aggregate.
- [ ] A rule change that drops recall below the threshold fails.
- [ ] The fixture is split into a tuning half and a held-out half.

**Test scenario:** Run the report on the fixture, then weaken a rule and assert the threshold failure.

## Out of scope

- Comparing against human moderators.
- Tuning on the test set without a held-out split.
