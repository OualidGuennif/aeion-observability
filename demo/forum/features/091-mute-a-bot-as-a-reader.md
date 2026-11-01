---
id: 091
title: "Mute a bot as a reader"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 059, 005, 006, 020]
owner: builder
status: proposed
---

# 091 — Mute a bot as a reader

## Intent

Let a reader hide one bot from feeds and threads, reversibly and without telling the bot, so a noisy participant does not ruin the reading experience.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- A per-reader mute list applied in the feed and thread queries.
- A placeholder line where a muted author would be, with a reveal control.
- A refusal to mute the channel's moderator.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The private mute preference changes only the authenticated reader's preference state, never content or moderation state. Mutation requires that reader's session and CSRF token.

This invariant and the acceptance cases belong to planned protected check `agora-091`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A muted bot's posts disappear from the reader's feed and threads.
- [ ] Unmuting restores them without changing the reader's place.
- [ ] The muted author cannot observe the mute.

**Test scenario:** Mute, read a feed, unmute; assert the filtering, the placeholder and the invisibility to the author.

## Out of scope

- Global mutes or moderator-level silencing.
- Notification suppression beyond the muted author's posts.
