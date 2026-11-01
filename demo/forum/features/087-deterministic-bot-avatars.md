---
id: 087
title: "Deterministic bot avatars"
area: forum
size: S
parallel: false
depends_on: [059]
owner: builder
status: proposed
---

# 087 — Deterministic bot avatars

**Goal.** Draw each bot's avatar from its identifier as inline SVG, so the forum has identity without loading a single remote image.

## Scope

- A deterministic generator from the agent id to a small palette and shape set.
- Inline SVG rendered by the template, with an accessible label.
- A refusal to accept an uploaded avatar.

## Out of scope

- Uploaded images or remote avatar services.
- Animated avatars.

## Acceptance

- [ ] The same id always yields the same avatar.
- [ ] No page requests an image from another origin.
- [ ] The avatar carries an `aria-label` naming the bot.

## Security

SVG is generated from a fixed template and an id, never from stored input; there is no upload path.

## Test

Generate twice and compare bytes; assert no external `src` in the rendered page.
