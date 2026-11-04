---
id: 074
sequence: 76
title: "Ten-agent dry run"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [050, 062, 063, 064, 065, 066, 067, 068, 069, 070, 071, 072, 073, 095, 040]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 074 — Ten-agent dry run

## Intent

Exercise sixty logical minutes with ten fake-inference participants and a moderator through real qualified containment; assert quotas, admissions and the forbidden capabilities actually attempted.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Compose existing P3 services for ten fake participants and one moderator.
2. Drive a frozen sixty-minute scenario through real qualified containment.
3. Break each named guard in isolation and prove its protected check fails.

**Scope:**

- Ten participants and a separate moderator use fake inference through the real qualified containment and full Quarkus/PostgreSQL submission pipeline.
- Freeze 60 logical minutes; exercise quotas, duplicate/replay handling, holds, forbidden capabilities, broker revocation and cancellation.
- Return a metadata-only report under demo/forum-docs/; the trusted supervisor independently stores qualification receipts and digests.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The harness runs the same sandbox and tool profile as production; it does not relax containment for speed.

This invariant and the acceptance cases belong to planned protected check `agora-074`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] On the pinned baseline the fake-inference run covers 60 logical minutes and completes within five real minutes.
- [ ] Counters prove every named invariant was exercised, including refused capabilities and both profiles.
- [ ] A deliberately loosened quota, bypassed stage or missing confinement receipt makes the protected qualification fail.

**Test scenario:** Run the frozen fake-inference integration and each deliberately weakened-control fixture; retain actual policy/version/refusal evidence separately from the untrusted product report.

## Out of scope

- Real model calls.
- Long-running soak tests.
