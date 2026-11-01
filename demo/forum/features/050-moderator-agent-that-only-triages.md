---
id: 050
title: "Moderator agent that only triages"
area: moderation
size: L
parallel: false
depends_on: [046]
owner: builder
status: proposed
---

# 050 — Moderator agent that only triages

**Goal.** Run a Flue tier-2 moderator that reads the queue, proposes a decision with its rule code, and asks the engine to apply it, so a model advises but never writes visibility.

## Scope

- A tool surface limited to reading a queue item, reading the rules and submitting a proposal.
- A server-side check that rejects a proposal with an unknown code or an action beyond the engine's.
- A per-run cap on proposals and a refusal to act twice on one item.

## Out of scope

- Free-form actions, shell access or database access from the agent.
- Deciding appeals.

## Acceptance

- [ ] A proposal without a valid rule code is refused and audited.
- [ ] The agent cannot change visibility when the engine disagrees.
- [ ] One queue item receives at most one applied proposal per run.

## Security

The agent's token can read the queue and submit proposals; it has no grant to write posts or moderate directly.

## Test

Replay a queue with a stub agent emitting a valid and an invalid proposal; assert application and refusal.
