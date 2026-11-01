---
id: 006
title: "CSRF protection on every mutation"
area: foundation
size: S
parallel: false
depends_on: [005]
owner: builder
status: proposed
---

# 006 — CSRF protection on every mutation

**Goal.** Require a double-submit token bound to the session for every state-changing request, including the agent API, so a cross-site form cannot act for a user.

## Scope

- Token issued per session, compared in constant time, accepted in a header or a form field.
- A middleware that refuses mutations without it before routing.
- An exemption list that contains only the internal agent API, authenticated by its own signed header.

## Out of scope

- CORS configuration for third-party callers.
- A token endpoint for SPA clients.

## Acceptance

- [ ] A POST without the token answers 403 and changes nothing.
- [ ] A token from another session is refused.
- [ ] GET requests are unaffected.

## Security

The token is not logged, not placed in URLs, and not accepted from query strings.

## Test

Exercise each mutation route without, with a foreign and with a valid token.
