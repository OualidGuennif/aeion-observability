---
id: 090
title: "Quote a comment"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [022, 020, 007, 063]
owner: builder
status: proposed
---

# 090 — Quote a comment

## Intent

Quote a short excerpt of another comment with a reference by id, so a reply keeps its context without copying a whole body.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- Reference a source comment visible to both the quoter and destination channel; cross-channel quotes are refused.
- Render a sanitized excerpt of at most 200 codepoints, truncating at a word boundary with an explicit marker.
- Recheck visibility on display: held/private sources redact the excerpt; a deleted public source may retain only a moderation-approved excerpt.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The source must be visible to the quoter at the time of quoting; the check is server-side.

This invariant and the acceptance cases belong to planned protected check `agora-090`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
