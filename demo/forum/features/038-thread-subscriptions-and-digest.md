---
id: 038
title: "Thread subscriptions and digest"
area: forum
size: M
parallel: false
depends_on: [028]
owner: builder
status: proposed
---

# 038 — Thread subscriptions and digest

**Goal.** Let an identity subscribe to a thread and receive one bounded digest instead of a notification per comment, so follow-up does not become noise.

## Scope

- A subscription table and a per-thread digest built on read.
- A cap on digest size with a count of what was omitted.
- Unsubscribe on the first click, without a login round trip.

## Out of scope

- Scheduled email delivery.
- Digests across several threads.

## Acceptance

- [ ] Ten comments produce one digest entry, not ten notifications.
- [ ] A digest over the cap states how many items were omitted.
- [ ] An unsubscribed thread produces nothing.

## Security

The unsubscribe link carries a signed token scoped to one subscription and one identity.

## Test

Subscribe, comment ten times, read the digest; assert the count, the cap and the unsubscribe effect.
