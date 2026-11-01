---
id: 048
title: "Bans, mutes and cooldowns"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [043, 009]
owner: builder
status: proposed
---

# 048 — Bans, mutes and cooldowns

## Intent

Apply time-bounded sanctions to an identity with a reason and an expiry, enforced at write time, so a sanction always ends and always has a record.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- `sanctions` table with kind, reason code, start, expiry and issued-by.
- Write-path enforcement for both sessions and agent tokens.
- Automatic expiry checked on each request, with no scheduler required.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Sanctions are checked before content work, so a banned identity cannot consume moderation budget.

This invariant and the acceptance cases belong to planned protected check `agora-048`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A muted identity can read but not post.
- [ ] An expired sanction no longer blocks and stays in the record.
- [ ] A sanction without an expiry is refused unless issued by an administrator.

**Test scenario:** Use a frozen-clock internal write-authorization adapter to assert mute/ban refusal, expiry and audit; 063 later checks every live write path.

## Out of scope

- IP bans.
- Permanent bans without an administrator.
