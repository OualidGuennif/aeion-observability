---
id: 049
title: "Escalation ladder"
area: moderation
size: S
parallel: false
depends_on: [048]
owner: builder
status: proposed
---

# 049 — Escalation ladder

**Goal.** Turn repeated upheld violations into warn, then mute, then ban, by a table with documented thresholds rather than a moderator's mood.

## Scope

- A ladder table keyed by upheld violations within a window.
- A single function returning the next sanction for an identity.
- A dry-run mode printing what would happen.

## Out of scope

- Machine-learning risk scores.
- Ladder changes without a review.

## Acceptance

- [ ] Three upheld violations in a week produce a mute, not a ban.
- [ ] The ladder resets after the window passes.
- [ ] The dry run matches the real outcome on the same fixture.

## Security

Only upheld decisions count; a dismissed report never escalates.

## Test

Simulate violations across the window boundary; assert each rung and the dry-run equality.
