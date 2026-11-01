---
id: 013
title: "Security headers and CSP"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 013 — Security headers and CSP

## Intent

Enforce CSP with per-response nonces and security headers from the first release; bounded violation reports are diagnostic, never a reason to ship report-only protection.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- CSP with `default-src 'self'`, nonce for the one inline script, no `unsafe-inline`.
- HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors 'none'`.
- A report endpoint that stores violations for a week.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The policy is generated per request; no template may hardcode a nonce.

This invariant and the acceptance cases belong to planned protected check `agora-013`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] CSP enforcement is active on the first served page: a script with its per-response nonce runs and one without it is blocked.
- [ ] Reports are bounded and store fixed violation codes and sanitized origins only, without arbitrary blocked-URI paths, queries or content.
- [ ] A report-only configuration cannot serve as the release default; a browser refusal test checks the enforcing header.

**Test scenario:** Fetch a page, assert the header set, and inject a script without the nonce in a headless browser to assert the block.

## Out of scope

- Third-party analytics or fonts.
- A CDN.
