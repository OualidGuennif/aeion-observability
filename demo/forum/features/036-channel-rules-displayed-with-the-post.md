---
id: 036
title: "Channel rules displayed with the post"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [019, 021, 041]
owner: builder
status: proposed
---

# 036 — Channel rules displayed with the post

## Intent

Show the rules a post was judged under, linked to their version, so a moderation decision is explainable to the reader and to an appeal.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- A rules version recorded with every post at creation.
- A rules page per channel rendering the version in force.
- A link from a held post to the exact rule that held it.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Rules are data with a version and a hash; a change is a reviewed commit, not a database edit.

This invariant and the acceptance cases belong to planned protected check `agora-036`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A fixture held with rule code R under rules version 2 cites code R and version 2 separately.
- [ ] Later rule changes leave the old post citation unchanged.
- [ ] Public-channel rules are public; private-channel rules remain subject to membership checks.

**Test scenario:** Post under two rule versions and assert each post cites its own version.

## Out of scope

- Per-user rule acceptance.
- Rule editing in the interface.
