---
id: 025
sequence: 25
title: "Full-text search"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [021, 020, 007]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 025 — Full-text search

## Intent

Search titles and bodies through Postgres full-text search with a sanitized query and a bounded result set, so search is useful without becoming an injection or scanning surface.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add PostgreSQL French text-search vectors and the GIN index.
2. Bind bounded query terms and sanitize snippets after visibility filtering.
3. Test operator-like input, private content denial and the frozen latency case.

**Scope:**

- A generated `tsvector` column with a GIN index and a French configuration.
- A query builder that escapes operators and caps terms and results.
- Snippets rendered through the sanitizer, never raw.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
