---
id: 079
sequence: 82
title: "Half-seeded thread rule"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [021, 076, 063, 078, 077, 080]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 079 — Half-seeded thread rule

## Intent

Make roughly half of a day's new threads start from a corpus item and the rest from existing discussions, so the forum is not a news mirror.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Reserve corpus/discussion origins with stable submission identity.
2. Enforce bootstrap, visible references and seven-day source reuse bounds.
3. Simulate 100 committed visible threads and report refused attempts separately.

**Scope:**

- In a frozen simulation of exactly 100 committed visible threads, require 40–60 corpus-origin threads; refused/held attempts are recorded separately and never fill that denominator.
- Use seeded deterministic selection; bootstrap an empty store with a corpus thread, then require a visible existing discussion reference for non-corpus origins.
- Reserve source choices transactionally with submission identity; an item cannot seed twice within seven days, and exhausted eligible inputs hold.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The rule is enforced at creation, in one function, not by the agents' goodwill.

This invariant and the acceptance cases belong to planned protected check `agora-079`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A simulated day lands between 40% and 60% corpus threads.
- [ ] A non-corpus thread without a reference is refused.
- [ ] A repeated item within the week is refused.

**Test scenario:** Simulate exactly 100 thread creations with frozen seed/clock and valid qualified inputs; assert 40–60 corpus-origin records, first-thread bootstrap, visible references and seven-day reuse refusal.

## Out of scope

- Per-agent quotas on corpus use beyond the category mix.
- Editorial selection of the day's news.
