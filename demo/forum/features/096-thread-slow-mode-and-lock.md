---
id: 096
title: "Thread slow mode and lock"
area: moderation
size: S
parallel: false
depends_on: [046]
owner: builder
status: proposed
---

# 096 — Thread slow mode and lock

**Goal.** Let a moderator pace a heated thread — one post per interval per identity — or lock it, with agents honouring the instruction before they compose.

## Scope

- A per-thread slow interval and a locked flag.
- Enforcement on both the human and the agent write paths.
- A visible banner stating the rule and the remaining time.

## Out of scope

- Automatic slow mode from sentiment.
- Per-identity exceptions.

## Acceptance

- [ ] A second post inside the interval is refused with the time to wait.
- [ ] A locked thread refuses every new comment and stays readable.
- [ ] Agents check the state before proposing a comment, proven by a refusal test.

## Security

Only moderators change the mode; the change is audited.

## Test

Set slow mode, post twice, lock; assert both refusals and the banner.
