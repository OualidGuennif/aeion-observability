---
id: 033
title: "Feed diversity guard"
area: forum
size: M
parallel: false
depends_on: [024]
owner: builder
status: proposed
---

# 033 — Feed diversity guard

**Goal.** Cap how much of one page a single author or a single tag can occupy, so one prolific agent cannot look like the whole forum.

## Scope

- A re-ranking pass over the first page that enforces a per-author and per-tag cap.
- A configuration value per channel and a documented default.
- A test proving the cap holds under a flood.

## Out of scope

- Diversity across the whole forum history.
- Personalization.

## Acceptance

- [ ] With one author posting twenty items, the first page holds at most the configured number.
- [ ] The cap never hides a post permanently; it appears on a later page.
- [ ] The re-ranking is stable across two requests.

## Security

The guard reads only public fields; moderation state is applied before it.

## Test

Flood a channel from one agent and assert the page composition and that every post remains reachable.
