---
id: 096
title: "Build telemetry and cost accounting"
area: build
size: M
parallel: true
depends_on: [091]
owner: builder
status: proposed
---

# 096 — Build telemetry and cost accounting

**Goal.** Emit one span per build step with tokens, model, tier, duration and estimated cost, and keep a per-feature and per-day total.

## Scope

- Spans through the collector with the existing allowlist keys.
- A cost table keyed by feature with the model's published rate.
- A refusal to report a cost when the token counts are missing.

## Out of scope

- Billing or invoicing.
- Comparing models.

## Acceptance

- [ ] A build produces spans for dispatch, gate and publish, all linked to one trace.
- [ ] The cost row sums the token counts and states the rate used.
- [ ] Missing usage yields an explicit unknown, never zero.

## Security

Telemetry carries counts and identifiers; the spec text and the diff never leave the host.

## Test

Run a stub build and assert the span names, the trace link and the cost arithmetic.
