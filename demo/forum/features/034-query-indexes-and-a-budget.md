---
id: 034
title: "Query indexes and a budget"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 034 — Query indexes and a budget

**Goal.** Index the read paths the feed and thread pages actually use, and pin a query budget with an EXPlaining test, so the forum stays fast without guesswork.

## Scope

- Indexes for channel feeds, thread children, votes by target and search.
- A test that runs `EXPLAIN` on the five hot queries and asserts index use and cost.
- A documented budget per endpoint.

## Out of scope

- Caching layers.
- Read replicas.

## Acceptance

- [ ] Each hot query's plan uses its index on a ten-thousand-post fixture.
- [ ] Removing an index makes the budget test fail, proving it is load-bearing.
- [ ] The budget is written next to the test.

## Security

No index on content hashes or moderation fields is exposed through a public route.

## Test

Run the plan assertions on a seeded fixture; drop one index in a scratch database and assert failure.
