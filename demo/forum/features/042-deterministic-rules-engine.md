---
id: 042
title: "Deterministic rules engine"
area: moderation
size: L
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [007, 032, 041]
owner: builder
status: proposed
---

# 042 — Deterministic rules engine

## Intent

Decide allow, hold or reject from normalized content, versioned rules and an explicit duplicate/rate snapshot; no model or I/O participates.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- Pure function inputs include normalized source, rules version/hash, duplicate score and bounded rate snapshot.
- Return canonical decision, primary rule code, severity and bounded evidence; stable rule priority resolves multiple matches.
- Evaluate the same normalized representation stored/rendered; missing signals or a check error hold the content.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Fail closed: a check that errors produces a hold, never an allow.

This invariant and the acceptance cases belong to planned protected check `agora-042`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
