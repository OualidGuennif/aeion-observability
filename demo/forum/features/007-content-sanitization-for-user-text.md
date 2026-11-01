---
id: 007
title: "Content sanitization for user text"
area: foundation
size: M
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 007 — Content sanitization for user text

**Goal.** Turn any submitted body into a small, safe HTML subset with length caps, so a post can never carry script, remote embeds or an oversized payload.

## Scope

- A Markdown subset renderer that escapes raw HTML and allows only paragraphs, emphasis, lists, quotes and code blocks.
- Length caps on characters and on rendered size.
- A normalization pass that strips control characters and collapses whitespace.

## Out of scope

- Images, tables, iframes or any remote resource.
- Client-side sanitization as the primary control.

## Acceptance

- [ ] A body containing a script tag, an event handler or a `javascript:` link renders inert text.
- [ ] A body over the cap is refused with a 413, not truncated silently.
- [ ] The same input always renders the same output.

## Security

Sanitization happens server-side before storage; the renderer is the only path from text to HTML.

## Test

A table of 30 known XSS payloads renders no element, no attribute and no script; a cap test asserts 413.
