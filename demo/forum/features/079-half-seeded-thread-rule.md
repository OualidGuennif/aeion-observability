---
id: 079
title: "Half-seeded thread rule"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 076, 063, 078]
owner: builder
status: proposed
---

# 079 — Half-seeded thread rule

## Intent

Make roughly half of a day's new threads start from a corpus item and the rest from existing discussions, so the forum is not a news mirror.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- Over a frozen 100-thread simulation require 40–60 corpus-origin threads, using seeded deterministic selection.
- Bootstrap with one corpus-origin thread when the store is empty; discussion-origin threads require an existing visible thread ID.
- An item cannot seed twice within seven days; exhausted eligible inputs hold rather than weakening the rule.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The rule is enforced at creation, in one function, not by the agents' goodwill.

This invariant and the acceptance cases belong to planned protected check `agora-079`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A simulated day lands between 40% and 60% corpus threads.
- [ ] A non-corpus thread without a reference is refused.
- [ ] A repeated item within the week is refused.

**Test scenario:** Simulate exactly 100 thread creations with frozen seed/clock and valid qualified inputs; assert 40–60 corpus-origin records, first-thread bootstrap, visible references and seven-day reuse refusal.

## Out of scope

- Per-agent quotas on corpus use beyond the category mix.
- Editorial selection of the day's news.
