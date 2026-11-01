---
id: 014
title: "Server-rendered templates"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 014 — Server-rendered templates

## Intent

Render every page on the server with auto-escaping templates, no CDN and no client framework, so the forum works without JavaScript and ships no bundle to attack.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- A template loader with auto-escaping on by default.
- A layout with navigation, flash messages and a strict form helper.
- Asset fingerprinting and long cache headers for static files.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Escaping is the default. The reviewed safe-output filter accepts only sanitizer-produced post/comment/corpus HTML, never arbitrary stored text.

This invariant and the acceptance cases belong to planned protected check `agora-014`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every page renders with JavaScript disabled.
- [ ] A template cannot emit unescaped input without an explicit, reviewed filter.
- [ ] Static assets carry a content hash in their name.

**Test scenario:** Render a page containing an escaped payload and assert the markup; assert the raw filter is used in one place only.

## Out of scope

- A single-page application or a JavaScript build step.
- Theming or user-supplied CSS.
