---
id: 077
title: "Two hundred synthetic French items"
area: corpus
size: M
parallel: true
phase: P4
tier: 3
write_paths: ["demo/forum/product/corpus/items/", "demo/forum/product/docs/corpus-style.md"]
depends_on: [075, 052]
owner: builder
status: proposed
---

# 077 — Two hundred synthetic French items

## Intent

Write two hundred plausible French news items across tech, state and government, clearly synthetic, so the forum has material without touching a real outlet.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- Exactly 200 validated synthetic French JSON items under corpus/items/, with invented source labels and no real-outlet quotations.
- At least forty items per each of the three categories, dates spanning six months and no personally identifying content.
- A style note only at docs/corpus-style.md; no app/schema/index changes, enabling parallel work with 082/086.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The corpus is data, never instructions; it is scanned by the injection guard like any body.

This invariant and the acceptance cases belong to planned protected check `agora-077`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every item validates against the schema and carries the label.
- [ ] No item names a real outlet as its source.
- [ ] Category counts meet the minimum.

**Test scenario:** Validate all items, then grep for a list of real outlet names to assert none appears as a source.

## Out of scope

- Any quotation of a real publication.
- Political advocacy or personally identifying content.
