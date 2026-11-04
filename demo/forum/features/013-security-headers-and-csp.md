---
id: 013
sequence: 13
title: "Security headers and CSP"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [001]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 013 — Security headers and CSP

## Intent

Enforce CSP and security headers for the React web application from its first release; fixed external scripts require no inline-script exception.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Apply production CSP and fixed security headers to web/API responses.
2. Support only required local assets and bounded optional reports.
3. Use a production browser build to prove inline/external script refusal.

**Scope:**

- Production CSP starts with default-src 'self', script-src 'self', object-src 'none', base-uri 'none' and frame-ancestors 'none'; never unsafe-inline or unsafe-eval.
- Use fingerprinted local JS/CSS assets. Only an actual reviewed inline script may require a fresh unpredictable per-response nonce; do not add inline scripts to satisfy this feature.
- HSTS applies over HTTPS; also X-Content-Type-Options, Referrer-Policy and fixed response headers on success and error paths.
- Bound any optional CSP reports and retain only fixed violation codes, sanitized origins and expiry, never arbitrary URI paths, queries or payloads.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Generate a nonce only when needed and never hardcode or cache it across personalized responses. The React production build must not require unsafe-inline or unsafe-eval.

This invariant and the acceptance cases belong to planned protected check `agora-013`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] In a production browser build the React application loads its same-origin scripts; an injected inline script and an external disallowed script are blocked.
- [ ] Headers are present on entry HTML and API success/error responses; a development-server exception cannot become production policy.
- [ ] If nonce-based inline code exists, a valid response nonce works and a missing/reused foreign nonce is blocked; otherwise no nonce or inline exception is required.
- [ ] Report payload canaries do not enter storage; report-only CSP cannot satisfy the enforcing release gate.

**Test scenario:** Use the real production browser build to verify allowed assets, blocked inline/external scripts and success/error headers; test report bounds and nonce behavior only where applicable.

## Out of scope

- Third-party analytics or fonts.
- A CDN.
