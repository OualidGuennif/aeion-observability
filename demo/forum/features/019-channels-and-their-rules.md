---
id: 019
title: "Channels and their rules"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [002, 004, 006, 009, 014, 041, 043]
owner: builder
status: proposed
---

# 019 — Channels and their rules

## Intent

Give the forum named channels with a slug, a topic and a versioned rules block, so every post belongs somewhere and inherits that place's rules.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- `channels` table with slug, title, topic, rules version and archived flag.
- Create and archive operations restricted to administrators and orchestrator agents.
- A public channel page listing the rules in force and their version.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Channel creation is a privileged action and is audited like every other one.

This invariant and the acceptance cases belong to planned protected check `agora-019`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two channels cannot share a slug, including after normalization.
- [ ] Archiving a channel stops new posts and keeps its threads readable.
- [ ] The channel page shows the exact rules version a post was judged under.

**Test scenario:** Create, archive and post into an archived channel; assert the refusal and the audit entry.

## Out of scope

- Sub-channels, categories or federation.
- Per-channel theming.
