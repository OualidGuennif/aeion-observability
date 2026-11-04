---
id: 010
sequence: 10
title: "Uniform error answers"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [001, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 010 — Uniform error answers

## Intent

Return a single problem-document shape with a correlation id, so failures are debuggable without leaking stack traces or internals.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Define the typed problem response and fixed error-code map.
2. Add correlation IDs without copying exception or request content.
3. Force validation, known-error and unexpected-error responses.

**Scope:**

- Problem JSON with type, title, status, code and correlation id.
- An exception handler that maps known errors and collapses the rest to 500.
- The correlation id echoed in a response header and written to the audit-adjacent log.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Errors and server logs carry fixed codes/correlation IDs only; arbitrary exception text, request bodies and tracebacks do not enter default logs or telemetry.

This invariant and the acceptance cases belong to planned protected check `agora-010`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An unhandled exception answers 500 with a correlation id and no traceback.
- [ ] Validation errors answer 422 with field paths but without values.
- [ ] The same correlation id appears in the server log line.

**Test scenario:** Force each error class and assert the shape, the status and the absence of internals.

## Out of scope

- Localized error messages.
- A public status page.
