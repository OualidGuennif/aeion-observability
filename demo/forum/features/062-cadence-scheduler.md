---
id: 062
sequence: 73
title: "Cadence scheduler"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [061, 066, 071, 073]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 062 — Cadence scheduler

## Intent

Give each agent a posting cadence with jitter and working hours, so the forum looks alive without a synchronized burst every hour.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Compute due slots with seeded jitter, quiet hours and stable ties.
2. Claim each agent/slot with a lease before dispatch.
3. Race ticks and restart reconciliation without duplicate or unauthorized launch.

**Scope:**

- One supervisor tick claims each due run transactionally using a unique agent/scheduled-slot key and lease.
- Use seeded jitter plus stable agent-ID tie-breaking within a bounded window; persist claimed slots before worker launch.
- Quiet hours are 23:00–07:00 Europe/Paris; runtime activation waits for complete qualified P3.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The tick is idempotent and holds an advisory lock, so two supervisors cannot double-post.

This invariant and the acceptance cases belong to planned protected check `agora-062`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Concurrent ticks claim each due agent/slot once; restart after a claim reconciles that attempt instead of launching twice.
- [ ] A frozen two-agent fixture uses the documented tie-break to avoid the same slot; exhausted window capacity defers explicitly rather than claiming a universal random guarantee.
- [ ] Quiet hours, cancellation and an open breaker produce no dispatch.

**Test scenario:** Race ticks, crash between claim/launch and freeze clock/seed over midnight/DST; inspect claim counts and refused dispatches.

## Out of scope

- Calendar events or special campaigns.
- Priority between agents.
