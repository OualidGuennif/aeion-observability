# 013 — Security headers on the forum JSON API (pinned target brief)

This is the adapted brief for feature **013 Security headers and CSP** against the runnable
Quarkus forum in `demo/forum-app/`. The canonical 100-feature contract in
[`features/013-security-headers-and-csp.md`](../features/013-security-headers-and-csp.md)
describes the planned server-rendered product; this brief is the one a build of the pinned
target is judged against.

## Intent

Every response from the forum JSON API carries an enforcing security-header set, including
refusals and errors. The policy is never report-only, and no response offers a browser surface
that would need a per-request nonce: the API serves JSON, not HTML.

## Inputs

- A JAX-RS response filter in `demo/forum-app/src/main/java/local/aeion/forum/` that adds, on
  every response:
  - `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: no-referrer`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- No `Content-Security-Policy-Report-Only` header, and no `unsafe-inline` in the policy.
- A JUnit/Quarkus test in `demo/forum-app/src/test/java/local/aeion/forum/` that checks a
  successful response and a refusal.

## Outputs

An artifact restricted to the two declared write scopes. The protected factory independently
validates it with `gradle test` and its own contract test copied in from outside the candidate
tree; a builder report cannot certify completion.

## Acceptance checks

- `GET /healthz` returns 200 with the enforcing CSP, `nosniff`, `no-referrer` and HSTS headers.
- `GET /api/threads/not-a-number` returns its refusal with the same headers.
- `Content-Security-Policy-Report-Only` is absent from both responses.
- The policy contains `default-src 'none'` and `frame-ancestors 'none'`, and no `unsafe-inline`.
- `gradle test` passes, including the protected `SecurityHeadersContractTest`.

## Out of scope

- A violation-report endpoint: the JSON API has no browser-rendered surface to report from.
- Per-response nonces: there is no inline script to authorise.
- Analytics, fonts, a CDN, or HTML templates.
