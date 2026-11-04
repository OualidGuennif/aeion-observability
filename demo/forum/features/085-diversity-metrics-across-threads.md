---
id: 085
sequence: 87
title: "Diversity metrics across threads"
area: corpus
size: S
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [084, 062, 067, 026]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 085 — Diversity metrics across threads

## Intent

Report per day how many distinct items, categories and authors appear in the first page of each channel, so 'looks alive' is measured.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Compute daily distinct-author/category and duplicate-rate aggregates.
2. Compare only known denominators against frozen synthetic targets.
3. Test exact recomputation, empty data and two consecutive measured misses.

**Scope:**

- Compute daily distinct-author, distinct-category and cross-author duplicate-rate metrics from authorized tables.
- Pin targets for the synthetic fixture: at least five authors, all three categories when available, duplicate rate at most 0.20.
- Show missing/empty denominators as unknown and flag two consecutive measured misses; do not infer semantic diversity from tags.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Metrics aggregate identifiers into counts; no body text is read.

This invariant and the acceptance cases belong to planned protected check `agora-085`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The metrics reproduce from the raw tables in a test.
- [ ] A day with one author everywhere reports the miss.
- [ ] The report names the channel and the metric, not a person.

**Test scenario:** Pin a day of data, compute, and compare with a hand-written expectation.

## Out of scope

- Per-reader ranking metrics.
- Model-based quality judgment.
