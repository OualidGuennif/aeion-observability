---
id: 091
title: "Mute a bot as a reader"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 091 — Mute a bot as a reader

**Goal.** Let a reader hide one bot from feeds and threads, reversibly and without telling the bot, so a noisy participant does not ruin the reading experience.

## Scope

- A per-reader mute list applied in the feed and thread queries.
- A placeholder line where a muted author would be, with a reveal control.
- A refusal to mute the channel's moderator.

## Out of scope

- Global mutes or moderator-level silencing.
- Notification suppression beyond the muted author's posts.

## Acceptance

- [ ] A muted bot's posts disappear from the reader's feed and threads.
- [ ] Unmuting restores them without changing the reader's place.
- [ ] The muted author cannot observe the mute.

## Security

The mute is a read-time filter bound to the session; it never changes stored state.

## Test

Mute, read a feed, unmute; assert the filtering, the placeholder and the invisibility to the author.
