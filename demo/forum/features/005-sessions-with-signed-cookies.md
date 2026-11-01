---
id: 005
title: "Sessions with signed cookies"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [004]
owner: builder
status: proposed
---

# 005 — Sessions with signed cookies

## Intent

Issue short-lived HttpOnly sessions whose identifier is rotated on login and privilege change, so a stolen cookie has a bounded life and a visible history.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- Signed session cookie with Secure, HttpOnly and SameSite=Lax.
- Server-side session rows with expiry, rotation and a logout-everywhere operation.
- Idle timeout and absolute lifetime, both configurable.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Signing keys come from the environment and rotate without invalidating every session at once.

This invariant and the acceptance cases belong to planned protected check `agora-005`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The cookie value is unreadable from JavaScript and rejected after logout.
- [ ] Logging in rotates the identifier and invalidates the previous session row.
- [ ] An expired session answers 401 without a redirect loop.

**Test scenario:** Log in, reuse the old cookie after rotation and assert 401; assert logout-everywhere kills all rows.

## Out of scope

- OAuth, OIDC or a third-party identity provider.
- Remember-me cookies beyond the absolute lifetime.
