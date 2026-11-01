---
id: 055
title: "Moderation red-team suite"
area: moderation
size: M
parallel: false
depends_on: [042]
owner: builder
status: proposed
---

# 055 — Moderation red-team suite

**Goal.** Keep a growing set of bypass attempts — homoglyphs, zero-width characters, encoded payloads, quote tricks — each pinned to the rule that must still catch it.

## Scope

- A fixture of at least forty bypass attempts with the expected verdict.
- A test that fails when a payload passes unflagged.
- A short note per case describing the trick.

## Out of scope

- Fuzzing in CI.
- Claims of complete coverage.

## Acceptance

- [ ] Every case has a verdict and a rule code.
- [ ] A newly added bypass that passes makes the suite red.
- [ ] The suite runs in under thirty seconds.

## Security

The suite is the regression net for the engine; it is never skipped in CI.

## Test

The suite itself, plus a deliberately weakened engine to prove it fails.
