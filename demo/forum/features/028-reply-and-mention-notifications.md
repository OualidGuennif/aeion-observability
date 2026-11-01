---
id: 028
title: "Reply and mention notifications"
area: forum
size: M
parallel: false
depends_on: [022]
owner: builder
status: proposed
---

# 028 — Reply and mention notifications

**Goal.** Notify an author when someone replies to their post or names them, with a bounded inbox and no notification for hidden or moderated content.

## Scope

- `notifications` table with recipient, kind, target and read flag.
- Generation on reply and on `@handle` mention, deduplicated per target.
- An inbox page with mark-all-read and a cap on unread items.

## Out of scope

- Push, email or websocket delivery.
- Mentions of non-existent handles creating accounts.

## Acceptance

- [ ] A reply creates one notification, not one per render.
- [ ] Mentioning an unknown handle notifies nobody and stores nothing.
- [ ] A hidden reply creates no notification.

## Security

Mentions resolve against exact handles only; a mention never triggers a lookup that reveals whether a hidden account exists.

## Test

Reply, mention and hide; assert the notification rows before and after each action.
