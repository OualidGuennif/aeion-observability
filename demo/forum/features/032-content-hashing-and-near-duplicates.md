---
id: 032
title: "Content hashing and near-duplicates"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 007]
owner: builder
status: proposed
---

# 032 — Content hashing and near-duplicates

## Intent

Hash every normalized body and detect near-duplicates with a shingle comparison, so spam and copy-paste floods are visible before they rank.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Store SHA-256 of normalized source; whitespace normalization is the shared sanitizer contract.
- Compute five-token shingles and Jaccard similarity; flag at score >= 0.80 within the last 24 hours.
- Return score/evidence as an engine input; do not decide visibility here.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Hashes never leave the database; neither the hash nor the score appears in telemetry.

This invariant and the acceptance cases belong to planned protected check `agora-032`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Pinned whitespace variants have identical normalized hashes.
- [ ] Named near-duplicate fixtures score at least 0.80 and unrelated fixtures below 0.80; this makes no semantic paraphrase guarantee.
- [ ] A 10000-post fixture meets a baseline and p95 budget recorded before qualification.

**Test scenario:** Use pinned whitespace variants and near-duplicate shingle fixtures with expected numeric Jaccard scores; check the 0.80 boundary and an unrelated sample, not semantic paraphrase detection.

## Out of scope

- Blocking on similarity, which is a moderation decision, not a storage one.
- Cross-language detection.
