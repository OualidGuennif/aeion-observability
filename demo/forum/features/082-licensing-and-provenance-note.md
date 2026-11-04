---
id: 082
sequence: 84
title: "Licensing and provenance note"
area: corpus
size: S
parallel: true
phase: P4
tier: 3
write_paths: ["demo/forum-docs/corpus-license.md"]
depends_on: [075]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 082 — Licensing and provenance note

## Intent

Document that the corpus is synthetic, how to replace it with licensed material, and what must change — so nobody ships real news through this path by accident.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Write the short synthetic-source and invented-label statement.
2. List attribution, licensing review and retention prerequisites for real sources.
3. Deliver only the documentation file with no runtime toggle.

**Scope:**

- Create only docs/corpus-license.md: synthetic-only statement, invented-source policy and review required for real sources.
- Document attribution, licensing review and retention prerequisites; do not introduce a real-source loader or deployment toggle.
- About-page integration belongs to 100; this documentation-only output is disjoint from 077/086.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

This note grants no runtime switch or real-source ingestion capability. 075/076 accept synthetic items only; future real-source support requires separate owner review.

This invariant and the acceptance cases belong to planned protected check `agora-082`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The note explicitly states all 200 items and their source labels are synthetic.
- [ ] The note lists attribution, licensing review and retention as prerequisites to real-source ingestion.
- [ ] The note can be added and reviewed without modifying app code, schemas or the corpus dataset.

**Test scenario:** Review the note against the three required prerequisites and synthetic-source statement; no runtime flag or about-page implementation is claimed by this documentation feature.

## Out of scope

- A licensed feed integration.
- Legal advice.
