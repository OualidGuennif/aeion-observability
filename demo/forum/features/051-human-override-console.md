---
id: 051
title: "Human override console"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [046, 005, 006, 009, 043]
owner: builder
status: proposed
---

# 051 — Human override console

## Intent

Let the administrator overturn any moderation action from one page, with a mandatory justification, so a wrong automated decision is one click from repair.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- A console listing recent actions with their evidence and a restore control.
- A mandatory free-text justification stored with the override.
- A confirmation step and a limit on overrides per minute.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The console requires a fresh session, and every view is audited.

This invariant and the acceptance cases belong to planned protected check `agora-051`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An override restores visibility and appends an audit entry citing the original action.
- [ ] An override without justification is refused.
- [ ] The console is unreachable for non-administrators, including by url.

**Test scenario:** Override a hold, assert restoration and audit; attempt the console as moderator and assert 403.

## Out of scope

- Editing audit rows.
- Overriding the audit chain itself.
