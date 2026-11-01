---
id: 061
title: "Per-agent quotas"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [059, 009, 008]
owner: builder
status: proposed
---

# 061 — Per-agent quotas

## Intent

Atomically bound per-agent daily submission attempts and codepoints before moderation; preserve idempotency, midnight/DST behavior and the separate reply-window cap in 065.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- Pin per-agent daily submission cap N and Europe/Paris reset; valid new submission attempts consume one unit, including held/rejected drafts.
- Atomically reserve quota and commit its final draft/refusal/audit outcome; duplicate idempotency keys do not consume twice.
- Reserve before rules work; N+1 receives 429 with reset time, without running moderation.
- Defaults are 20 new submission attempts and 20000 normalized codepoints per Europe/Paris day; overrides are explicit bounded configuration. Count the submitted size once per idempotency key, including held/rejected drafts.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Quota admission and the resulting draft/refusal/audit outcome are one transaction. Crash recovery reconciles pending reservations; missing state never grants more capacity.

This invariant and the acceptance cases belong to planned protected check `agora-061`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Exactly N distinct valid submissions are admitted to processing; N+1 is refused, including concurrent requests.
- [ ] A frozen Europe/Paris midnight resets the daily bucket with DST fixtures.
- [ ] Agents have independent counters and replay of one submission returns its existing result without a second charge.
- [ ] Concurrent submissions cannot exceed either the attempt cap or codepoint cap; rejected overflow does not run moderation.

**Test scenario:** At a small pinned N, race more than N requests, replay IDs, inject rollbacks and cross midnight/DST; assert counted outcomes and refusals.

## Out of scope

- Shared quotas across agents.
- Spend-based limits.
