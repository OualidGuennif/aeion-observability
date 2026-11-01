---
id: 073
title: "Agent activity audit"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [009, 012, 059]
owner: builder
status: proposed
---

# 073 — Agent activity audit

## Intent

Record every agent run with its inputs' identifiers, decisions and outcome, so the cockpit can show what each bot did without storing what it read.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- One audit entry per run: agent, started, finished, drafts submitted, refusals by code.
- A per-agent history view for administrators.
- A join with the telemetry trace id.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The audit references identifiers; content stays in Postgres and never enters telemetry.

This invariant and the acceptance cases belong to planned protected check `agora-073`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A run with two drafts and one refusal commits one final activity record with those counts, keyed by run ID.
- [ ] The trace ID matches the supervisor-issued ID; backend outage records pending/unknown receipt rather than inventing a stored trace.
- [ ] No body, prompt or tool payload is recorded.

**Test scenario:** Run a stub agent and assert the entry's counts, the trace link and the absence of text.

## Out of scope

- Storing model output.
- Per-token logs.
