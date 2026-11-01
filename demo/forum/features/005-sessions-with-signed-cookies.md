---
id: 005
title: "Sessions with signed cookies"
area: foundation
size: M
parallel: false
depends_on: [004]
owner: builder
status: proposed
---

# 005 — Sessions with signed cookies

**Goal.** Issue short-lived HttpOnly sessions whose identifier is rotated on login and privilege change, so a stolen cookie has a bounded life and a visible history.

## Scope

- Signed session cookie with Secure, HttpOnly and SameSite=Lax.
- Server-side session rows with expiry, rotation and a logout-everywhere operation.
- Idle timeout and absolute lifetime, both configurable.

## Out of scope

- OAuth, OIDC or a third-party identity provider.
- Remember-me cookies beyond the absolute lifetime.

## Acceptance

- [ ] The cookie value is unreadable from JavaScript and rejected after logout.
- [ ] Logging in rotates the identifier and invalidates the previous session row.
- [ ] An expired session answers 401 without a redirect loop.

## Security

Signing keys come from the environment and rotate without invalidating every session at once.

## Test

Log in, reuse the old cookie after rotation and assert 401; assert logout-everywhere kills all rows.
