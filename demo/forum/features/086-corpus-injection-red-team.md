---
id: 086
title: "Corpus injection red-team"
area: corpus
size: M
parallel: false
depends_on: [076, 052]
owner: builder
status: proposed
---

# 086 — Corpus injection red-team

**Goal.** Prove that a hostile corpus item cannot steer a bot: each payload is loaded, posted and asserted inert at the agent boundary.

## Scope

- At least twenty payload items: instructions, role markers, tool-call imitations, delimiter escapes.
- Assertion that the bot's available tools and its next action are unchanged.
- A regression check that a new payload class is added when one is found.

## Out of scope

- Exhaustive adversarial research.
- Blocking the item from readers.

## Acceptance

- [ ] Every payload reaches the agent with its instruction spans neutralized.
- [ ] No payload changes a tool list, a quota or a rule decision.
- [ ] The suite runs in CI on every corpus change.

## Security

This is the evidence that the corpus is data; without it the claim is a promise.

## Test

The suite itself, plus a deliberately unguarded loader to prove it fails.
