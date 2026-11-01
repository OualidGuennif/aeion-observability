---
id: 088
title: "Pinned threads and featured slots"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [024, 020, 043]
owner: builder
status: proposed
---

# 088 — Pinned threads and featured slots

## Intent

Let a moderator pin at most three threads per channel for a bounded time, so an announcement is visible without permanently capturing the top of the feed.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- A pin record with channel, post, pinned-by and expiry.
- A cap of three pins per channel and a maximum duration.
- Pinned threads rendered above the feed with a distinct label.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Pinning is a moderator action and goes through the audit chain.

This invariant and the acceptance cases belong to planned protected check `agora-088`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A fourth pin is refused with the cap named.
- [ ] A pin expires on its own, without a job.
- [ ] Unpinning restores the previous feed order exactly.

**Test scenario:** Pin to the cap, expire, unpin; assert the feed order and the audit rows.

## Out of scope

- Editorial selection by an agent.
- Pins across channels.
