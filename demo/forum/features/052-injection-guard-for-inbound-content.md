---
id: 052
title: "Injection guard for inbound content"
area: moderation
size: L
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 052 — Injection guard for inbound content

**Goal.** Treat every post, comment and corpus excerpt as untrusted text: scan it for instruction-shaped payloads, strip them from what an agent reads, and keep the raw text only in the database.

## Scope

- A scanner flagging imperative instructions, role markers, delimiter tricks and encoded payloads.
- A sanitized excerpt passed to any agent, with the flagged spans replaced by a marker.
- A refusal to feed untrusted text into a tool-calling context at all.

## Out of scope

- Blocking posts on suspicion; the guard protects agents, not readers.
- Guaranteeing detection of every payload.

## Acceptance

- [ ] A post containing `ignore previous instructions` reaches an agent with that span replaced.
- [ ] The original text remains visible to readers and moderators unchanged.
- [ ] A guard error refuses to hand text to an agent.

## Security

Untrusted text is data: no instruction from it can change a tool call, a policy, or a system prompt.

## Test

A corpus of thirty injection payloads, each asserted at the agent boundary; plus a false-positive set of ordinary French sentences.
