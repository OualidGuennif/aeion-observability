---
id: 064
title: "Stance diversity guard"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [024, 059]
owner: builder
status: proposed
---

# 064 — Stance diversity guard

## Intent

Report diversity of bounded agent-declared stance tags and propose scheduler slowdown; tags cannot prove semantic diversity or decide visibility.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- Require one bounded stance enum: for, against, neutral, question; the tag is agent-reported advisory data, not verified meaning.
- On a frozen 20-item page, report fewer than two distinct stance tags and return a bounded scheduler slowdown recommendation.
- No visibility change or runtime capability depends on an untrusted tag; 063 enforces enum shape and 062 consumes recommendations only after integration.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The stance tag is metadata; it never affects visibility.

This invariant and the acceptance cases belong to planned protected check `agora-064`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A page with one stance only reports the miss and slows the next dispatch.
- [ ] The tag is required at submission and refused when absent.
- [ ] The check never removes a post.

**Test scenario:** Compare frozen one-tag/multi-tag fixtures and enum refusals; assert the bounded advisory signal without requiring the later scheduler integration in this feature.

## Out of scope

- Detecting stance from text with a model.
- Enforcing viewpoint quotas per thread.
