---
id: 083
sequence: 85
title: "Topic interest weighting"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [060, 076, 078]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 083 — Topic interest weighting

## Intent

Use reviewed finite category weights with seeded selection and quota availability; qualify the fixed three-category distribution without claiming distinct arbitrary random draws.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Validate and normalize finite reviewed persona category weights.
2. Select among positive-weight available categories under existing quotas.
3. Pin combined distributions and report incompatible availability as degraded.

**Scope:**

- Use the category-weight fields already declared by 060; normalize finite nonnegative weights and reject an all-zero vector.
- Use a seeded weighted picker; quota availability from 078 bounds which categories are eligible.
- With suitable available items and positive combined weights, the fixed 300-selection daily fixture covers exactly the three schema categories.

**required_categories:** tech, state, government.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Weights are configuration; they never come from user input.

This invariant and the acceptance cases belong to planned protected check `agora-083`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A zero tech weight excludes tech for that persona; quotas cannot silently override a zero weight. No eligible positive weight returns explicit degraded/unavailable.
- [ ] Two frozen contrasting personas reproduce their registered category counts; no claim is made about arbitrary random draws.
- [ ] Across the declared combined positive-weight fixture, all three schema categories are covered within 078 tolerance; incompatible persona availability reports degraded coverage rather than faking compliance.

**Test scenario:** Draw a day for three personas and assert the distributions and the diversity check.

## Out of scope

- Learning weights from engagement.
- Per-user interests.
