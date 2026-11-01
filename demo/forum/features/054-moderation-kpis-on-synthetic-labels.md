---
id: 054
title: "Moderation KPIs on synthetic labels"
area: moderation
size: M
parallel: false
depends_on: [046]
owner: builder
status: proposed
---

# 054 — Moderation KPIs on synthetic labels

**Goal.** Score the engine and the moderator agent against a labelled fixture with precision and recall, so a change to rules is measured rather than assumed.

## Scope

- A labelled fixture of two hundred items with expected codes.
- A command computing precision, recall and confusion by rule code.
- A threshold below which the check fails.

## Out of scope

- Comparing against human moderators.
- Tuning on the test set without a held-out split.

## Acceptance

- [ ] The report names the per-code confusion, not only the aggregate.
- [ ] A rule change that drops recall below the threshold fails.
- [ ] The fixture is split into a tuning half and a held-out half.

## Security

The fixture is synthetic and labelled; it is not benchmark evidence about any real community.

## Test

Run the report on the fixture, then weaken a rule and assert the threshold failure.
