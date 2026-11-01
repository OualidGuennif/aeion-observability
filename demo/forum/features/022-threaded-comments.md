---
id: 022
title: "Threaded comments"
area: forum
size: M
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 022 — Threaded comments

**Goal.** Support replies three levels deep with a stable ordering, so a thread reads topically and a deep reply cannot be used to bury or hide context.

## Scope

- `comments` table with post, parent, depth, author and body.
- A depth cap of three with a clear refusal, and chronological ordering within a parent.
- A reply form that keeps the parent visible.

## Out of scope

- Infinite nesting or collapsing threads.
- Comment editing after a reply exists.

## Acceptance

- [ ] A fourth-level reply is refused with a message naming the cap.
- [ ] Replying to a hidden comment is refused.
- [ ] The rendered order is stable across two requests.

## Security

A comment inherits its post's visibility; there is no comment-level channel check that could disagree.

## Test

Build a four-deep chain and a reply to a hidden parent; assert both refusals and the stable ordering.
