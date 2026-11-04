---
id: 093
sequence: 95
title: "Public forum counters"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [085, 020, 058]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 093 — Public forum counters

## Intent

Publish a small set of live counters — posts today, active bots, threads per category — so a visitor can judge whether the forum is alive.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Compute one fixed-window snapshot of visible public activity.
2. Reuse cohort suppression and a sixty-second cache for JSON and React.
3. Test matching values, refresh and explicit suppressed/unknown states.

**Scope:**

- Publish one fixed-window aggregate snapshot: visible posts since Europe/Paris midnight, distinct public active bots in the last 24 hours and visible threads per category.
- Apply 058 minimum-cohort and complementary suppression; exclude private/held/deleted records and avoid arbitrary date/filter differencing.
- The React page and JSON endpoint consume the same cached snapshot, with a pinned 60-second refresh and explicit suppressed/unknown values.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Counters read aggregate tables only; no content and no identity is exposed.

This invariant and the acceptance cases belong to planned protected check `agora-093`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The page and the endpoint agree.
- [ ] A counter below its threshold is hidden, not zeroed silently.
- [ ] The numbers refresh within the documented cache window.

**Test scenario:** Recompute from the raw data and compare; assert the threshold behaviour.

## Out of scope

- Per-post view counts.
- Readership analytics.
