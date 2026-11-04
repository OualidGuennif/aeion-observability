---
id: 006
sequence: 6
title: "CSRF protection on every mutation"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [005]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 006 — CSRF protection on every mutation

## Intent

Protect every cookie-authenticated mutation with a session-bound CSRF token; keep the credential-isolated internal agent API on its separate authenticated path.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Define session-bound CSRF bootstrap for the React browser.
2. Enforce it on cookie mutations and isolate the broker-authenticated exemption.
3. Exercise missing, foreign and valid tokens on every mutation path.

**Scope:**

- Provide an authenticated same-origin CSRF bootstrap endpoint for the React client; token remains in memory and is bound to the current session.
- Compare the header token in constant time before routing any cookie-authenticated mutation, including login/session transitions under an explicit pre-session CSRF protocol.
- Only the internal broker-authenticated agent API is exempt. It refuses human session credentials; no GET or URL token may authorize a mutation.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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

- Third-party browser callers or permissive credentialed CORS.
- Persisting session credentials or CSRF tokens in localStorage.
