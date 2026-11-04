---
id: 034
sequence: 39
title: "Query indexes and a budget"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [021, 022, 023, 025]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 034 — Query indexes and a budget

## Intent

Index the read paths the feed and thread pages actually use, and pin a query budget with an EXPlaining test, so the forum stays fast without guesswork.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Record five actual hot queries on the pinned PostgreSQL fixture.
2. Add only indexes needed by their fixed plan/buffer/latency budgets.
3. Remove each designated index in a negative test and prove its check fails.

**Scope:**

- Indexes for channel feeds, thread children, votes by target and search.
- A test that runs `EXPLAIN` on the five hot queries and asserts index use and cost.
- A documented budget per endpoint.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

No index on content hashes or moderation fields is exposed through a public route.

This invariant and the acceptance cases belong to planned protected check `agora-034`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Each hot query's plan uses its index on a ten-thousand-post fixture.
- [ ] Removing an index makes the budget test fail, proving it is load-bearing.
- [ ] The budget is written next to the test.

**Test scenario:** Pin Postgres version, fixture, five query plans and buffer/latency budgets; remove each load-bearing index and verify its designated regression check fails without forcing planner settings.

## Out of scope

- Caching layers.
- Read replicas.
