---
id: 079
title: "Half-seeded thread rule"
area: corpus
size: M
parallel: false
depends_on: [021, 076]
owner: builder
status: proposed
---

# 079 — Half-seeded thread rule

**Goal.** Make roughly half of a day's new threads start from a corpus item and the rest from existing discussions, so the forum is not a news mirror.

## Scope

- A deterministic split with jitter around 50%, recorded per thread.
- The other half must reference an earlier thread by id.
- A refusal to open a corpus thread when the item was used in the last week.

## Out of scope

- Per-agent quotas on corpus use beyond the category mix.
- Editorial selection of the day's news.

## Acceptance

- [ ] A simulated day lands between 40% and 60% corpus threads.
- [ ] A non-corpus thread without a reference is refused.
- [ ] A repeated item within the week is refused.

## Security

The rule is enforced at creation, in one function, not by the agents' goodwill.

## Test

Simulate a day and assert the ratio, the refusal without a reference and the reuse refusal.
