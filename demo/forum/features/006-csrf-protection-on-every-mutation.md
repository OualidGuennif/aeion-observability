---
id: 006
title: "CSRF protection on every mutation"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [005]
owner: builder
status: proposed
---

# 006 — CSRF protection on every mutation

## Intent

Require a double-submit token bound to the session for every state-changing request, including the agent API, so a cross-site form cannot act for a user.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- Token issued per session, compared in constant time, accepted in a header or a form field.
- A middleware that refuses mutations without it before routing.
- An exemption list that contains only the internal agent API, authenticated by its own signed header.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

CSRF tokens are session-bound, compared in constant time and never accepted through URLs. Agent exemptions authenticate a revocable identity at the trusted broker and cannot use session credentials.

This invariant and the acceptance cases belong to planned protected check `agora-006`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A POST without the token answers 403 and changes nothing.
- [ ] A token from another session is refused.
- [ ] GET requests are unaffected.

**Test scenario:** Exercise each mutation route without, with a foreign and with a valid token.

## Out of scope

- CORS configuration for third-party callers.
- A token endpoint for SPA clients.
