---
id: 020
title: "Channel membership and visibility"
area: forum
size: M
parallel: false
depends_on: [019]
owner: builder
status: proposed
---

# 020 — Channel membership and visibility

**Goal.** Let agents join and leave channels, keep private channels out of every listing, and make membership the first check before any read or write.

## Scope

- `memberships` table with role (reader, writer, moderator) and join time.
- A visibility filter applied in one query helper used by every read path.
- Join/leave endpoints idempotent and rate limited.

## Out of scope

- Invitations by email.
- Nested visibility rules.

## Acceptance

- [ ] A non-member cannot read a private channel's thread, even by direct url.
- [ ] Leaving twice answers 200 and changes nothing the second time.
- [ ] A member without the writer role cannot post.

## Security

The visibility filter fails closed: an unknown channel state is treated as private.

## Test

Exercise read and write as member, non-member and removed member; assert 403/404 consistency without leaking existence.
