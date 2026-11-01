---
id: 037
title: "Permalinks and canonical URLs"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 037 — Permalinks and canonical URLs

**Goal.** Give every post, comment and channel one canonical path and redirect the others, so links survive renaming and nothing is reachable by two names.

## Scope

- Slug-based canonical urls with a numeric id fallback.
- A redirect from an old slug to the canonical one, and a 404 for an unknown id.
- A `rel=canonical` tag on every page.

## Out of scope

- Custom vanity urls.
- Cross-channel moves.

## Acceptance

- [ ] Renaming a post redirects the old path permanently.
- [ ] An unknown slug and an unknown id both answer 404, identical in shape.
- [ ] Every listing links to the canonical form only.

## Security

A slug is normalized to a safe character set before it is stored or routed.

## Test

Rename a post and request both paths; assert the redirect, the canonical tag and the identical 404s.
