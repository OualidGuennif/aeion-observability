---
id: 075
sequence: 77
title: "Corpus item schema"
area: corpus
size: S
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [002, 007, 029]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 075 — Corpus item schema

## Intent

Define one news item — synthetic title, category, date, short excerpt, source label — with a stable id, so every later corpus feature shares one shape.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Define the strict three-category synthetic item DTO and bounds.
2. Validate IDs/dates/labels and make URL-like text inert.
3. Reject missing synthetic flags, unknown categories, extra fields and oversize text.

**Scope:**

- Strict schema: stable id, category enum tech/state/government, bounded title/excerpt/source_label, ISO date and synthetic=true.
- Pin title 120, excerpt 1000 and source_label 80 codepoints; extra fields are refused.
- Validate at load time and in tests; an invented source label is mandatory.

**categories:** tech, state, government.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

A URL field is not supported, and URL-shaped text in every free-text field is rendered inert by 007/029. No item is fetched or interpreted as an instruction.

This invariant and the acceptance cases belong to planned protected check `agora-075`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An item without the synthetic flag is refused.
- [ ] An unknown category is refused.
- [ ] An excerpt above the cap is rejected, not truncated silently.

**Test scenario:** Validate a good item and four malformed ones; assert the exact refusals.

## Out of scope

- Real sources or attributed quotes.
- Images or media.
