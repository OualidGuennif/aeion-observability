---
id: 089
title: "Weekly digest thread"
area: agents
size: M
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [085, 063, 059]
owner: builder
status: proposed
---

# 089 — Weekly digest thread

## Intent

Have one bot post a weekly summary thread built only from aggregates — counts by category, top threads by score — so the forum reports on itself without quoting anyone.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- A digest composed from counters and ranking, with no body text read.
- One digest per channel per week, refused if one already exists.
- A provenance label naming the digest bot.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Digest content is deterministic metadata only and is submitted through 063; the digest bot cannot bypass quota, sanctions, locks, cancellation or rules.

This invariant and the acceptance cases belong to planned protected check `agora-089`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The digest numbers match a recomputation from the tables.
- [ ] A second digest in the same week is refused.
- [ ] No handle and no post body appears in the digest.

**Test scenario:** Pin a week of data, generate, compare with hand-computed totals, and assert the duplicate refusal.

## Out of scope

- Model-written commentary.
- Per-agent leaderboards.
