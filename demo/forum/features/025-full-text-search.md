---
id: 025
title: "Full-text search"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 020, 007]
owner: builder
status: proposed
---

# 025 — Full-text search

## Intent

Search titles and bodies through Postgres full-text search with a sanitized query and a bounded result set, so search is useful without becoming an injection or scanning surface.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- A generated `tsvector` column with a GIN index and a French configuration.
- A query builder that escapes operators and caps terms and results.
- Snippets rendered through the sanitizer, never raw.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Parameters are bound, never interpolated; snippets are sanitized like any body.

This invariant and the acceptance cases belong to planned protected check `agora-025`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A query with operators or quotes returns results instead of an error.
- [ ] A non-member's search never returns a private post.
- [ ] A thousand-post fixture answers in under 100 ms on the recorded baseline.

**Test scenario:** Search with operator-like input, as a member and a non-member; assert results, refusal and timings.

## Out of scope

- Fuzzy matching, synonyms or a search service.
- Search over private channels for non-members.
