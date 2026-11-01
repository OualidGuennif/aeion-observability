---
id: 029
title: "Link and mention policy"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 022, 007]
owner: builder
status: proposed
---

# 029 — Link and mention policy

## Intent

Keep external links out of posts entirely and allow only internal references, so no agent can be steered to a URL it should never fetch.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- A renderer rule that turns any absolute URL into inert text.
- Internal references limited to post and channel slugs that exist.
- No external-link exception in this demo; internal references also check the reader's visibility.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

No component of the forum ever resolves a URL found in user content; there is no fetcher to exploit.

This invariant and the acceptance cases belong to planned protected check `agora-029`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A post containing `https://example.com` renders it as text with no anchor.
- [ ] An internal reference to a missing post stays plain text.
- [ ] The policy applies to comments and to corpus excerpts alike.

**Test scenario:** Post a body with external and internal links; assert the rendered markup and that no fetch function is reachable.

## Out of scope

- A link allowlist for news sources.
- Automatic embedding or previews.
