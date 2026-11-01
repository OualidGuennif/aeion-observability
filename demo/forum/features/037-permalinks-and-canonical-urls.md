---
id: 037
title: "Permalinks and canonical URLs"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 020]
owner: builder
status: proposed
---

# 037 — Permalinks and canonical URLs

## Intent

Give every post, comment and channel one canonical path and redirect the others, so links survive renaming and nothing is reachable by two names.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Slug-based canonical urls with a numeric id fallback.
- A redirect from an old slug to the canonical one, and a 404 for an unknown id.
- A `rel=canonical` tag on every page.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

A slug is normalized to a safe character set before it is stored or routed.

This invariant and the acceptance cases belong to planned protected check `agora-037`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
