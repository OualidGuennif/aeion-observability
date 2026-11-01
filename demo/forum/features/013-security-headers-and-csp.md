---
id: 013
title: "Security headers and CSP"
area: foundation
size: S
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 013 — Security headers and CSP

**Goal.** Send a strict Content-Security-Policy with per-request nonces plus HSTS, frame denial and a referrer policy, first in report-only, then enforcing.

## Scope

- CSP with `default-src 'self'`, nonce for the one inline script, no `unsafe-inline`.
- HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors 'none'`.
- A report endpoint that stores violations for a week.

## Out of scope

- Third-party analytics or fonts.
- A CDN.

## Acceptance

- [ ] A page with the nonce loads its script; without it, the browser blocks it.
- [ ] A violation report is stored with the blocked URI but no query string.
- [ ] Enforcing mode ships after a week of clean reports.

## Security

The policy is generated per request; no template may hardcode a nonce.

## Test

Fetch a page, assert the header set, and inject a script without the nonce in a headless browser to assert the block.
