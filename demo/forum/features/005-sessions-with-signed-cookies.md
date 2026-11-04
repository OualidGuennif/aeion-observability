---
id: 005
sequence: 5
title: "Sessions with signed cookies"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [004]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 005 — Sessions with signed cookies

## Intent

Issue short-lived HttpOnly sessions whose identifier is rotated on login and privilege change, so a stolen cookie has a bounded life and a visible history.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Add opaque server-side sessions and the protected cookie contract.
2. Implement login rotation, expiry and logout without browser token storage.
3. Test old-cookie refusal, expiry and logout-everywhere.

**Scope:**

- Signed session cookie with Secure, HttpOnly and SameSite=Lax.
- Server-side session rows with expiry, rotation and a logout-everywhere operation.
- Idle timeout and absolute lifetime, both configurable.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
