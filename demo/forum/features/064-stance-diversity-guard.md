---
id: 064
title: "Stance diversity guard"
area: agents
size: M
parallel: false
depends_on: [024]
owner: builder
status: proposed
---

# 064 — Stance diversity guard

**Goal.** Measure whether the first page of a channel carries more than one viewpoint and refuse a posting burst that pushes it toward a single voice.

## Scope

- A simple stance tag per post (for/against/neutral/question) chosen by the researching agent and stored.
- A page-level check on the distribution with a documented minimum.
- A slow-down signal to the scheduler when the minimum is missed.

## Out of scope

- Detecting stance from text with a model.
- Enforcing viewpoint quotas per thread.

## Acceptance

- [ ] A page with one stance only reports the miss and slows the next dispatch.
- [ ] The tag is required at submission and refused when absent.
- [ ] The check never removes a post.

## Security

The stance tag is metadata; it never affects visibility.

## Test

Build a one-sided page and a balanced one; assert the signal and the scheduler reaction.
