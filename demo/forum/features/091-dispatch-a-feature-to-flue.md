---
id: 091
title: "Dispatch a feature to Flue"
area: build
size: L
parallel: true
depends_on: [090]
owner: builder
status: proposed
---

# 091 — Dispatch a feature to Flue

**Goal.** Turn a queued feature into one Flue run with the spec as its brief, the declared tier, a bounded toolset and a hard time limit.

## Scope

- A run request carrying feature id, spec path, tier and the acceptance section.
- A result contract: changed paths, checks requested, a short summary.
- A hard timeout and a refusal to start a second run for the same feature.

## Out of scope

- Free-form chat with the builder.
- Model choice beyond the relay's configured model.

## Acceptance

- [ ] A dispatch produces a run record with a trace id and a started state.
- [ ] A second dispatch of the same feature is refused while it runs.
- [ ] A run over the time limit is stopped and marked failed.

## Security

The run goes through the relay; the sandbox never receives the provider key.

## Test

Dispatch with a stub runner; assert the record, the refusal and the timeout path.
