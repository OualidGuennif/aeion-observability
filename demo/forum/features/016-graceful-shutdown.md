---
id: 016
title: "Graceful shutdown"
area: foundation
size: S
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 016 — Graceful shutdown

**Goal.** Drain in-flight requests and close the pool on SIGTERM within a bounded time, so a deploy never cuts a write in half.

## Scope

- A signal handler that stops accepting, waits for in-flight work and closes the pool.
- A configurable deadline after which the process exits anyway.
- A log line per phase with a duration.

## Out of scope

- Zero-downtime blue-green orchestration.
- Job draining beyond HTTP requests.

## Acceptance

- [ ] A slow request started before SIGTERM completes.
- [ ] A request arriving after SIGTERM is refused promptly.
- [ ] The process exits within the deadline even with a stuck handler.

## Security

Shutdown logs carry durations and counts, never request content.

## Test

Start a slow request, send SIGTERM and assert the response completes and the exit code is 0.
