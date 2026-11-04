---
id: 086
sequence: 88
title: "Corpus injection red-team"
area: corpus
size: M
parallel: true
phase: P4
tier: 3
write_paths: ["demo/forum-app/src/test/resources/corpus_injection/", "demo/forum-app/src/test/java/local/aeion/forum/CorpusInjectionTest.java"]
depends_on: [076, 052, 066]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 086 — Corpus injection red-team

## Intent

Test hostile corpus fixtures against excerpt filtering and independently enforced capabilities; content may affect drafts but cannot enlarge authority.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Add twenty hostile corpus data fixtures and one isolated JUnit class.
2. Exercise known-span filtering and independent broker capability refusals.
3. Weaken filtering and authorization separately and require both regressions to fail.

**Scope:**

- At least twenty synthetic payloads under demo/forum-app/src/test/resources/corpus_injection/ and one isolated JUnit test class CorpusInjectionTest.java.
- Assert declared known-span filtering plus independently enforced broker refusal of forbidden tools, identity changes, quotas and destinations.
- Do not assert that model wording or next action stays identical; protection means unchanged authority, not unchanged reasoning.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

This is the evidence that the corpus is data; without it the claim is a promise.

This invariant and the acceptance cases belong to planned protected check `agora-086`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Known payload fixtures get their declared spans filtered; a guard error refuses delivery.
- [ ] Both known and unknown payload shapes cannot enlarge broker capabilities, identity, destinations, quotas or the versioned rules configuration.
- [ ] Protected qualification runs the suite for every corpus change; weakening the guard/broker fixture produces a failure.

**Test scenario:** Run the twenty-payload fixture plus unknown injection shapes; weaken the broker or known-span filter separately and require its designated protected assertion to fail.

## Out of scope

- Exhaustive adversarial research.
- Blocking the item from readers.
