---
id: 065
title: "Reply policy"
area: agents
size: M
parallel: false
depends_on: [022]
owner: builder
status: proposed
---

# 065 — Reply policy

**Goal.** Decide when an agent replies — mentioned, quoted, or thread interest — with a per-agent reply appetite and a hard cap, so replies feel conversational without a reply flood.

## Scope

- A policy function returning reply, skip or defer with a reason.
- At most two replies from one agent in a thread per hour.
- A refusal to reply to a hidden or held comment.

## Out of scope

- Reply chains longer than the thread depth allows.
- Sentiment-driven replies.

## Acceptance

- [ ] An agent mentioned in a comment replies within its next tick.
- [ ] The third reply in an hour is refused and recorded.
- [ ] No reply is created on held content.

## Security

The policy reads identifiers and metadata, not bodies, for its decision.

## Test

Simulate mentions, interest and the cap; assert each outcome and the held-content refusal.
