---
id: 055
sequence: 56
title: "Moderation red-team suite"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [042]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 055 — Moderation red-team suite

## Intent

Keep a growing set of bypass attempts — homoglyphs, zero-width characters, encoded payloads, quote tricks — each pinned to the rule that must still catch it.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Add forty named encoded/Unicode/quote bypass fixtures.
2. Bind each to the reviewed rule and expected fixed verdict.
3. Weaken one rule and prove the corresponding protected assertion fails.

**Scope:**

- A fixture of at least forty bypass attempts with the expected verdict.
- A test that fails when a payload passes unflagged.
- A short note per case describing the trick.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The suite is the regression net for the engine; it is never skipped in CI.

This invariant and the acceptance cases belong to planned protected check `agora-055`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

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
