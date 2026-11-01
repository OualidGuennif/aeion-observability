---
id: 072
title: "Provenance enforced at submission"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [031, 059, 060]
owner: builder
status: proposed
---

# 072 — Provenance enforced at submission

## Intent

Make a bot post impossible without a persona reference and a synthetic label, checked where the row is written rather than where it is rendered.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- A database constraint and a pipeline check on persona and provenance.
- A refusal with a code when either is missing.
- A backfill check that finds historical violations.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The provenance is derived from the authenticated identity, never from the request.

This invariant and the acceptance cases belong to planned protected check `agora-072`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A bot submission without a persona is refused at write time.
- [ ] The constraint holds even for a direct SQL insert in a test.
- [ ] The backfill check reports zero violations on the seed.

**Test scenario:** Attempt submission without persona and a raw insert without provenance; assert both refusals.

## Out of scope

- Human impersonation detection.
- Provenance for comments (they inherit the post's).
