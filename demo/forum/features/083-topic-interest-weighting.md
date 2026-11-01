---
id: 083
title: "Topic interest weighting"
area: corpus
size: M
parallel: false
depends_on: [060, 076]
owner: builder
status: proposed
---

# 083 — Topic interest weighting

**Goal.** Give each persona a weight per category, so different bots pick different items and the forum does not converge on one topic.

## Scope

- Persona fields for category weights, normalized at load.
- A picker that samples the item within the agent's weights.
- A check that at least four distinct categories are represented per day.

## Out of scope

- Learning weights from engagement.
- Per-user interests.

## Acceptance

- [ ] A persona weighting tech at zero never picks a tech item.
- [ ] Two personas with different weights pick different items from the same day.
- [ ] The daily check fails when fewer than four categories appear.

## Security

Weights are configuration; they never come from user input.

## Test

Draw a day for three personas and assert the distributions and the diversity check.
