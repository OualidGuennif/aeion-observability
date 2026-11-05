---
id: 037
sequence: 32
title: "Permalinks and canonical URLs"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [021, 020, 022]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 037 — Permalinks and canonical URLs

## Intent

Give every post, comment and channel one canonical path and redirect the others, so links survive renaming and nothing is reachable by two names.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Define canonical channel/post/comment routes from safe slugs and IDs.
2. Handle old-path redirects and production React deep links.
3. Test rename, canonical metadata and visibility-preserving unknown routes.

**Scope:**

- Slug-based canonical urls with a numeric id fallback.
- A redirect from an old slug to the canonical one, and a 404 for an unknown id.
- A `rel=canonical` tag on every page.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

A slug is normalized to a safe character set before it is stored or routed.

This invariant and the acceptance cases belong to planned protected check `agora-037`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Renaming a post redirects the old path permanently.
- [ ] An unknown slug and an unknown id both answer 404, identical in shape.
- [ ] Every listing links to the canonical form only.

**Test scenario:** Rename a post and request both paths; assert the redirect, the canonical tag and the identical 404s.

## Out of scope

- Custom vanity urls.
- Cross-channel moves.
