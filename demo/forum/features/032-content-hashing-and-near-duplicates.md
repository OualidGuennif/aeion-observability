---
id: 032
sequence: 30
title: "Content hashing and near-duplicates"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [021, 007]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 032 — Content hashing and near-duplicates

## Intent

Hash every normalized body and detect near-duplicates with a shingle comparison, so spam and copy-paste floods are visible before they rank.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Hash the shared normalized source and compute bounded five-token shingles.
2. Return exact/Jaccard duplicate evidence without changing visibility.
3. Pin numeric threshold boundaries and the declared comparison window.

**Scope:**

- Store SHA-256 of normalized source; whitespace normalization is the shared sanitizer contract.
- Compute five-token shingles and Jaccard similarity; flag at score >= 0.80 within the last 24 hours.
- Return score/evidence as an engine input; do not decide visibility here.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Hashes never leave the database; neither the hash nor the score appears in telemetry.

This invariant and the acceptance cases belong to planned protected check `agora-032`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Pinned whitespace variants have identical normalized hashes.
- [ ] Named near-duplicate fixtures score at least 0.80 and unrelated fixtures below 0.80; this makes no semantic paraphrase guarantee.
- [ ] A 10000-post fixture meets a baseline and p95 budget recorded before qualification.

**Test scenario:** Verify in JUnit fixtures using pinned whitespace variants, 0.80 Jaccard boundary samples, unrelated samples, and the 10000-post baseline p95 budget (not HTTP latency timing).

## Out of scope

- Blocking on similarity, which is a moderation decision, not a storage one.
- Cross-language detection.
