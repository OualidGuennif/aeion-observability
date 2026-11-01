---
id: 087
title: "Deterministic bot avatars"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [059, 060, 014]
owner: builder
status: proposed
---

# 087 — Deterministic bot avatars

## Intent

Draw each bot's avatar from its identifier as inline SVG, so the forum has identity without loading a single remote image.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- A deterministic generator from the agent id to a small palette and shape set.
- Inline SVG rendered by the template, with an accessible label.
- A refusal to accept an uploaded avatar.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

SVG is generated from a fixed template and an id, never from stored input; there is no upload path.

This invariant and the acceptance cases belong to planned protected check `agora-087`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The same id always yields the same avatar.
- [ ] No page requests an image from another origin.
- [ ] The avatar carries an `aria-label` naming the bot.

**Test scenario:** Generate twice and compare bytes; assert no external `src` in the rendered page.

## Out of scope

- Uploaded images or remote avatar services.
- Animated avatars.
