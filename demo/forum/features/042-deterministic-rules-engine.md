---
id: 042
sequence: 45
title: "Deterministic rules engine"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [007, 032, 041]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 042 — Deterministic rules engine

## Intent

Decide allow, hold or reject from normalized content, versioned rules and an explicit duplicate/rate snapshot; no model or I/O participates.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Define one pure input snapshot and canonical allow/hold/reject result.
2. Implement only the reviewed deterministic rules with explicit priorities.
3. Pin forty cases including missing/error signals; add no model or I/O.

**Scope:**

- Pure function inputs include normalized source, rules version/hash, duplicate score and bounded rate snapshot.
- Return canonical decision, primary rule code, severity and bounded evidence; stable rule priority resolves multiple matches.
- Evaluate the same normalized representation stored/rendered; missing signals or a check error hold the content.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Fail closed: a check that errors produces a hold, never an allow.

This invariant and the acceptance cases belong to planned protected check `agora-042`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Identical complete input snapshots yield byte-identical verdicts, including a stable allow code.
- [ ] Every verdict has one primary code from the versioned registry.
- [ ] Unknown input shapes reject; missing signals and exceptions hold, including zero-width/encoded bypass fixtures.

**Test scenario:** A table of at least forty inputs with expected verdicts and codes, including the failing-check path.

## Out of scope

- Semantic understanding or toxicity scoring by a model.
- Automatic bans from the engine.
