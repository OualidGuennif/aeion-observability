---
id: 069
title: "Bot memory checkpoint"
area: agents
size: M
parallel: false
depends_on: [059]
owner: builder
status: proposed
---

# 069 — Bot memory checkpoint

**Goal.** Store one bounded working checkpoint per bot per run in claude-mem — what it read, what it decided — so a later run continues without replaying a transcript.

## Scope

- Save and read through the explicit API with `platformSource: "pi"`.
- A checkpoint schema: last threads, open drafts, refusals received.
- A size cap with a documented truncation order.

## Out of scope

- Long-term knowledge in claude-mem.
- Cross-bot memory sharing.

## Acceptance

- [ ] A second run reads the checkpoint written by the first.
- [ ] The checkpoint never exceeds the cap and records what was dropped.
- [ ] A missing checkpoint starts clean, never fails the run.

## Security

The checkpoint stores identifiers and short notes, never full post bodies.

## Test

Write, read back and truncate; assert the round trip and the cap behaviour.
