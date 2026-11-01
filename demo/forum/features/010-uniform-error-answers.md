---
id: 010
title: "Uniform error answers"
area: foundation
size: S
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 010 — Uniform error answers

**Goal.** Return a single problem-document shape with a correlation id, so failures are debuggable without leaking stack traces or internals.

## Scope

- Problem JSON with type, title, status, code and correlation id.
- An exception handler that maps known errors and collapses the rest to 500.
- The correlation id echoed in a response header and written to the audit-adjacent log.

## Out of scope

- Localized error messages.
- A public status page.

## Acceptance

- [ ] An unhandled exception answers 500 with a correlation id and no traceback.
- [ ] Validation errors answer 422 with field paths but without values.
- [ ] The same correlation id appears in the server log line.

## Security

No stack trace, SQL text, file path or secret reaches the client.

## Test

Force each error class and assert the shape, the status and the absence of internals.
