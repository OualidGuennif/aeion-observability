---
id: 012
title: "Forum telemetry through the collector"
area: foundation
size: M
parallel: false
depends_on: [001, 011]
owner: builder
status: proposed
---

# 012 — Forum telemetry through the collector

**Goal.** Export forum spans to the existing OTel collector with the same attribute allowlist, so the forum appears in Langfuse without adding a second pipeline.

## Scope

- An OTLP/HTTP exporter pointed at the collector, with batching and a bounded queue.
- A span helper that refuses an attribute outside the collector's allowlist at development time.
- Resource attributes limited to `service.name`.

## Out of scope

- Content, identifiers of posts, or any user text in telemetry.
- A new collector or a new Langfuse project.

## Acceptance

- [ ] A forum request produces one span visible through `GET /api/public/v2/observations`.
- [ ] A disallowed attribute is rejected by the development assertion.
- [ ] The exporter being down never fails the request.

## Security

Telemetry carries codes and counts only; a post's text never leaves Postgres.

## Test

Emit a span with a forbidden attribute and assert refusal; read the trace back through the observations API.
