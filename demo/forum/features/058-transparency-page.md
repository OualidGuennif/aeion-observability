---
id: 058
sequence: 59
title: "Transparency page"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [053, 014]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 058 — Transparency page

## Intent

Publish aggregate moderation counts — held, rejected, restored, appeals upheld — from the audit trail, so the forum's own behaviour is visible without exposing content.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Compute fixed-window public moderation aggregates through restricted SQL.
2. Apply minimum-cohort and complementary suppression before JSON/UI output.
3. Test independent counts, private-event exclusion and reconstruction attempts.

**Scope:**

- A public React page displays weekly rule-code aggregates from a separate restricted aggregation query, not arbitrary audit row access.
- Pin a minimum cohort k=5 and suppress complementary totals/cells that would reconstruct a suppressed count; private-channel events never enter public aggregates.
- Publish one fixed-window cached snapshot and its generation timestamp; do not expose arbitrary filters for differencing small cohorts.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Aggregation happens in SQL over codes and timestamps only; no content column is read.

This invariant and the acceptance cases belong to planned protected check `agora-058`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Authorized counts match an independent recomputation before suppression; private-channel events contribute nothing.
- [ ] Cells smaller than five and reconstructing complementary totals are suppressed explicitly, never displayed as zero.
- [ ] The page and backing JSON contain no handle, target ID or individual moderator identity.

**Test scenario:** Compute twice and assert equality with the raw query; assert bucketing under the threshold.

## Out of scope

- Per-post histories in public.
- Naming moderators.
