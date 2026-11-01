---
id: 088
title: "Pinned threads and featured slots"
area: forum
size: S
parallel: false
depends_on: [024]
owner: builder
status: proposed
---

# 088 — Pinned threads and featured slots

**Goal.** Let a moderator pin at most three threads per channel for a bounded time, so an announcement is visible without permanently capturing the top of the feed.

## Scope

- A pin record with channel, post, pinned-by and expiry.
- A cap of three pins per channel and a maximum duration.
- Pinned threads rendered above the feed with a distinct label.

## Out of scope

- Editorial selection by an agent.
- Pins across channels.

## Acceptance

- [ ] A fourth pin is refused with the cap named.
- [ ] A pin expires on its own, without a job.
- [ ] Unpinning restores the previous feed order exactly.

## Security

Pinning is a moderator action and goes through the audit chain.

## Test

Pin to the cap, expire, unpin; assert the feed order and the audit rows.
