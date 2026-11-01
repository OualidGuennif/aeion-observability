---
id: 007
title: "Content sanitization for user text"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 007 — Content sanitization for user text

## Intent

Turn any submitted body into a small, safe HTML subset with length caps, so a post can never carry script, remote embeds or an oversized payload.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- A Markdown subset renderer that escapes raw HTML and allows only paragraphs, emphasis, lists, quotes and code blocks.
- Length caps on characters and on rendered size.
- A normalization pass that strips control characters and collapses whitespace.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Retain normalized plain Markdown and sanitizer-produced HTML, never original transport bytes. HTML is escaped by the renderer. The same normalized representation is used by rules and rendering.

This invariant and the acceptance cases belong to planned protected check `agora-007`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Script, event-handler and javascript-URL inputs render inert text, never executable HTML.
- [ ] More than 4000 codepoints or 32768 rendered bytes is refused with 413; no silent truncation.
- [ ] Normalization and rendering are byte-stable for pinned fixtures, including zero-width and code-block cases.

**Test scenario:** A table of 30 known XSS payloads renders no element, no attribute and no script; a cap test asserts 413.

## Out of scope

- Images, tables, iframes or any remote resource.
- Client-side sanitization as the primary control.
