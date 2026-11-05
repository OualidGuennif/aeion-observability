---
id: 054
sequence: 55
title: "Moderation KPIs on synthetic labels"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [046]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 054 — Moderation KPIs on synthetic labels

## Intent

Measure deterministic-engine precision/recall on a held-out labelled synthetic fixture; moderator-proposal comparison is optional only after 050 is qualified.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Freeze separate tuning and held-out synthetic label sets.
2. Compute per-code confusion, denominators and precision/recall.
3. Weaken a rule and prove the held-out threshold fails without retuning labels.

**Scope:**

- Two hundred labelled synthetic cases split by stable IDs into 100 tuning and 100 held-out cases.
- Report engine per-code confusion, precision and recall; optional moderator proposal evaluation waits for qualified 050.
- Pin minimum recall 0.95 and precision 0.95 on the held-out synthetic set, with denominators and unknown cases explicit.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The fixture is synthetic and labelled; it is not benchmark evidence about any real community.

This invariant and the acceptance cases belong to planned protected check `agora-054`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

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
