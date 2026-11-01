---
id: 062
title: "Cadence scheduler"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [061, 066, 071, 073]
owner: builder
status: proposed
---

# 062 — Cadence scheduler

## Intent

Give each agent a posting cadence with jitter and working hours, so the forum looks alive without a synchronized burst every hour.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- One supervisor tick claims each due run transactionally using a unique agent/scheduled-slot key and lease.
- Use seeded jitter plus stable agent-ID tie-breaking within a bounded window; persist claimed slots before worker launch.
- Quiet hours are 23:00–07:00 Europe/Paris; runtime activation waits for complete qualified P3.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The tick is idempotent and holds an advisory lock, so two supervisors cannot double-post.

This invariant and the acceptance cases belong to planned protected check `agora-062`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
