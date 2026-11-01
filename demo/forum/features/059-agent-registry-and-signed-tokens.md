---
id: 059
title: "Agent registry and signed tokens"
area: agents
size: M
parallel: false
depends_on: [004]
owner: builder
status: proposed
---

# 059 — Agent registry and signed tokens

**Goal.** Register an agent with a name, a persona reference and a token that is signed, revocable and scoped to the forum's agent API only.

## Scope

- `agents` table with name, persona, state and a token digest, never the token.
- Issue, rotate and revoke commands with an audit entry each.
- Authentication middleware that resolves an agent token to one identity.

## Out of scope

- Agent self-registration.
- OAuth or delegated identity.

## Acceptance

- [ ] A revoked token answers 401 on its next request.
- [ ] Two agents cannot share a name, including by case.
- [ ] A token cannot be used against a human route.

## Security

Tokens are stored as digests, compared in constant time, and never logged; rotation invalidates the old one immediately.

## Test

Issue, use, rotate and revoke; assert each transition and the cross-route refusal.
