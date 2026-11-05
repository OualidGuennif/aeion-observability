---
id: 090
sequence: 92
title: "Quote a comment"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [022, 020, 007, 063]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 090 — Quote a comment

## Intent

Quote a short excerpt of another comment with a reference by id, so a reply keeps its context without copying a whole body.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Validate same-channel visible source and destination references.
2. Render the bounded sanitized excerpt with explicit truncation.
3. Test later hiding, deletion and the required approval for a retained excerpt.

**Scope:**

- Reference a source comment visible to both the quoter and destination channel; cross-channel quotes are refused.
- Render a sanitized excerpt of at most 200 codepoints, truncating at a word boundary with an explicit marker.
- Recheck visibility on display: held/private sources redact the excerpt; a deleted public source may retain only a moderation-approved excerpt.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The source must be visible to the quoter at the time of quoting; the check is server-side.

This invariant and the acceptance cases belong to planned protected check `agora-090`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An excerpt over 200 codepoints is truncated at a word boundary with a marker, not rejected for length.
- [ ] Quoting a held/private/cross-channel source is refused; later loss of visibility redacts the rendered excerpt.
- [ ] Deleting an otherwise public source preserves only a permitted sanitized excerpt and marks the source unavailable.

**Test scenario:** Quote a visible, a held and a deleted comment; assert acceptance, refusal and fallback.

## Out of scope

- Nested quote chains.
- Quoting across channels.
