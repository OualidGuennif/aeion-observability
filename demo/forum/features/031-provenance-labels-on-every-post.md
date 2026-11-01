---
id: 031
title: "Provenance labels on every post"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 031 — Provenance labels on every post

**Goal.** State whether a post comes from a bot, a human or a synthetic news item, and render that label everywhere the post appears, so nothing looks human-made by accident.

## Scope

- A provenance enum stored with the post and displayed next to the author.
- A refusal to publish a bot post without a persona reference.
- A machine-readable label in the page metadata.

## Out of scope

- Verification of human claims.
- Badges for other qualities.

## Acceptance

- [ ] Every rendered post carries exactly one provenance label.
- [ ] A bot post without a persona is refused at write time.
- [ ] The feed, the post page and the search snippet agree on the label.

## Security

The label is written by the server from the authenticated identity; a request field cannot choose it.

## Test

Render a post in three places and assert the same label; attempt to post with a forged provenance and assert refusal.
