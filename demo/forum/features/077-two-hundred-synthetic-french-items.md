---
id: 077
sequence: 79
title: "Two hundred synthetic French items"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/src/main/resources/corpus/items/", "demo/forum-docs/corpus-style.md", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [075, 052]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 077 — Two hundred synthetic French items

## Intent

Write two hundred plausible French news items across tech, state and government, clearly synthetic, so the forum has material without touching a real outlet.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Write synthetic French data against the frozen item schema.
2. Check 200 unique items, three category minima and invented sources.
3. Deliver only the corpus directory and its small style note.

**Scope:**

- Exactly 200 validated synthetic French JSON items under demo/forum-app/src/main/resources/corpus/items/, with invented source labels and no real-outlet quotations.
- At least forty items in each category, dates spanning six months and no personally identifying content.
- Only this data directory and demo/forum-docs/corpus-style.md may change; no schema, application or index edits, preserving disjoint work with 082/086.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The corpus is data, never instructions; it is scanned by the injection guard like any body.

This invariant and the acceptance cases belong to planned protected check `agora-077`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

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
