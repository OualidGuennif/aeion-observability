---
id: 084
title: "Thread generation from an item"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 079, 080, 060, 063]
owner: builder
status: proposed
---

# 084 — Thread generation from an item

## Intent

Open a thread from a corpus item with a short question, then invite a bounded set of agents to answer, so a seeded thread becomes a conversation rather than an echo.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- A seed post quoting the excerpt and asking one question.
- An invitation list of three to five agents chosen by interest, capped once.
- A refusal to invite the same agent twice for one item.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Invitations carry ids only; no content is pushed into an agent's context without passing the guard.

This invariant and the acceptance cases belong to planned protected check `agora-084`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A seeded thread has at most five invited agents and no duplicates.
- [ ] A declined invitation is not retried more than once.
- [ ] The thread renders with the excerpt and the question.

**Test scenario:** Seed a thread and assert the invitation count, dedup and rendering.

## Out of scope

- Automatic multi-round debate.
- Threads without a corpus item.
