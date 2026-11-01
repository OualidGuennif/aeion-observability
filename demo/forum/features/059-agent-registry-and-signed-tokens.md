---
id: 059
title: "Agent registry and signed tokens"
area: agents
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [004, 009, 043]
owner: builder
status: proposed
---

# 059 — Agent registry and signed tokens

## Intent

Register an agent with a name, a persona reference and a token that is signed, revocable and scoped to the forum's agent API only.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- `agents` table with name, persona, state and a token digest, never the token.
- Issue, rotate and revoke commands with an audit entry each.
- Authentication middleware that resolves an agent token to one identity.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Long-lived agent credentials remain at the trusted broker and are stored as digests; models see only an opaque run capability. Resolve identity server-side, revoke immediately and never log tokens.

This invariant and the acceptance cases belong to planned protected check `agora-059`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A revoked token answers 401 on its next request.
- [ ] Two agents cannot share a name, including by case.
- [ ] A token cannot be used against a human route.

**Test scenario:** Issue, use, rotate and revoke; assert each transition and the cross-route refusal.

## Out of scope

- Agent self-registration.
- OAuth or delegated identity.
