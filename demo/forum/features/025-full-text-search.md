---
id: 025
title: "Full-text search"
area: forum
size: M
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 025 — Full-text search

**Goal.** Search titles and bodies through Postgres full-text search with a sanitized query and a bounded result set, so search is useful without becoming an injection or scanning surface.

## Scope

- A generated `tsvector` column with a GIN index and a French configuration.
- A query builder that escapes operators and caps terms and results.
- Snippets rendered through the sanitizer, never raw.

## Out of scope

- Fuzzy matching, synonyms or a search service.
- Search over private channels for non-members.

## Acceptance

- [ ] A query with operators or quotes returns results instead of an error.
- [ ] A non-member's search never returns a private post.
- [ ] A thousand-post fixture answers in under 100 ms on the recorded baseline.

## Security

Parameters are bound, never interpolated; snippets are sanitized like any body.

## Test

Search with operator-like input, as a member and a non-member; assert results, refusal and timings.
