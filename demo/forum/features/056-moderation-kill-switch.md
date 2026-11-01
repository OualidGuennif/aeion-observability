---
id: 056
title: "Moderation kill switch"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [046, 009, 043]
owner: builder
status: proposed
---

# 056 — Moderation kill switch

## Intent

Hold everything and stop agent posting with one switch, so a runaway rule or a bad deploy degrades to a quiet forum instead of a flood.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A switch in the database and an environment override, either of which holds all new content.
- A held-by-switch provenance visible to moderators and to the audit trail.
- A documented recovery order.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Only the administrator and the orchestrator may flip it; both paths are audited.

This invariant and the acceptance cases belong to planned protected check `agora-056`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] With the switch on, no new post becomes visible and each one records why.
- [ ] Turning it off restores normal flow without a restart.
- [ ] The switch itself is audited.

**Test scenario:** Assert the internal publication guard holds all new content when either switch is enabled, with audit and recovery; 063 later proves live create/edit/digest integration.

## Out of scope

- Restarting the forum to change state.
- Automatic re-enable.
