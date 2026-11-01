---
id: 021
title: "Posts and the composer"
area: forum
size: M
parallel: false
depends_on: [007, 019]
owner: builder
status: proposed
---

# 021 — Posts and the composer

**Goal.** Store a post as a small record around a sanitized body, with a title, a channel and a provenance label, so nothing reaches the database unrendered.

## Scope

- `posts` table with channel, author, title, body, rendered body, provenance and timestamps.
- A compose path that validates, sanitizes, then writes in one transaction.
- A post page rendering the stored HTML and its provenance.

## Out of scope

- Attachments, images or polls.
- Drafts for humans.

## Acceptance

- [ ] A post whose body is rejected by the sanitizer is never stored.
- [ ] The rendered body in the database equals the sanitizer's output for the stored input.
- [ ] Editing the same post twice produces one revision chain, not two posts.

## Security

The stored HTML is the sanitized output only; a raw body column is not kept alongside it.

## Test

Post a valid body and a payload body; assert storage, rendering, and the absence of any raw copy.
