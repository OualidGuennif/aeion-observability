---
id: 086
title: "Corpus injection red-team"
area: corpus
size: M
parallel: true
phase: P4
tier: 3
write_paths: ["demo/forum/product/tests/fixtures/corpus_injection/", "demo/forum/product/tests/test_corpus_injection.py"]
depends_on: [076, 052, 066]
owner: builder
status: proposed
---

# 086 — Corpus injection red-team

## Intent

Test hostile corpus fixtures against excerpt filtering and independently enforced capabilities; content may affect drafts but cannot enlarge authority.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- At least twenty synthetic injection fixtures under tests/fixtures/corpus_injection/ and one isolated test module.
- Assert known-span filtering plus server-side refusal of forbidden tools, identity changes, quotas and destination overrides.
- Do not require model wording or next action to stay identical; successful security means unchanged authority, not unchanged reasoning.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

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
