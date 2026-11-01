---
id: 014
title: "Server-rendered templates"
area: foundation
size: S
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 014 — Server-rendered templates

**Goal.** Render every page on the server with auto-escaping templates, no CDN and no client framework, so the forum works without JavaScript and ships no bundle to attack.

## Scope

- A template loader with auto-escaping on by default.
- A layout with navigation, flash messages and a strict form helper.
- Asset fingerprinting and long cache headers for static files.

## Out of scope

- A single-page application or a JavaScript build step.
- Theming or user-supplied CSS.

## Acceptance

- [ ] Every page renders with JavaScript disabled.
- [ ] A template cannot emit unescaped input without an explicit, reviewed filter.
- [ ] Static assets carry a content hash in their name.

## Security

Escaping is the default; the one raw filter is used only for the sanitized body of a post.

## Test

Render a page containing an escaped payload and assert the markup; assert the raw filter is used in one place only.
