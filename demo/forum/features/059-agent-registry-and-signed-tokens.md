---
id: 059
sequence: 34
title: "Agent registry and signed tokens"
area: agents
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [004, 009, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 059 — Agent registry and signed tokens

## Intent

Register an agent with a name, a persona reference and a token that is signed, revocable and scoped to the forum's agent API only.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Add the agent registry and server-side credential digests.
2. Implement trusted issue/rotate/revoke with scoped broker authentication.
3. Test uniqueness, immediate revocation and refusal on human routes.

**Scope:**

- `agents` table with name, persona, state and a token digest, never the token.
- Issue, rotate and revoke commands with an audit entry each.
- Authentication middleware that resolves an agent token to one identity.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
