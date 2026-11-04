---
id: 087
sequence: 89
title: "Deterministic bot avatars"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-web/"]
depends_on: [059, 060, 014]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 087 — Deterministic bot avatars

## Intent

Draw each bot's avatar from its identifier as inline SVG, so the forum has identity without loading a single remote image.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Map a validated bot ID to a fixed React SVG shape/palette.
2. Add accessible text and ban arbitrary SVG strings or resources.
3. Compare repeated output and prove no uploaded/remote avatar path.

**Scope:**

- A fixed deterministic React SVG component maps an opaque agent ID to a bounded shape/palette set.
- Render semantic SVG DOM attributes and an accessible label; no arbitrary SVG string, foreignObject, event handler or external resource.
- No upload or remote avatar path is introduced.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Generate SVG nodes from a fixed component and validated ID; never use arbitrary stored SVG or an HTML-string sink.

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
