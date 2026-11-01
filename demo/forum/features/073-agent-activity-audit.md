---
id: 073
title: "Agent activity audit"
area: agents
size: S
parallel: false
depends_on: [009]
owner: builder
status: proposed
---

# 073 — Agent activity audit

**Goal.** Record every agent run with its inputs' identifiers, decisions and outcome, so the cockpit can show what each bot did without storing what it read.

## Scope

- One audit entry per run: agent, started, finished, drafts submitted, refusals by code.
- A per-agent history view for administrators.
- A join with the telemetry trace id.

## Out of scope

- Storing model output.
- Per-token logs.

## Acceptance

- [ ] A run that submits two drafts and receives one refusal writes one entry with those counts.
- [ ] The entry links to a trace that exists.
- [ ] No body text is recorded.

## Security

The audit references identifiers; content stays in Postgres and never enters telemetry.

## Test

Run a stub agent and assert the entry's counts, the trace link and the absence of text.
