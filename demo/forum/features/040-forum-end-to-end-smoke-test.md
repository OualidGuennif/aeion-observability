---
id: 040
title: "Forum end-to-end smoke test"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [039, 005, 006, 009, 012, 020, 025, 031, 059, 060]
owner: builder
status: proposed
---

# 040 — Forum end-to-end smoke test

## Intent

Qualify the P1 read-only fixture forum through HTTP/browser flows; publication remains refused until the separate full P3 scenario in 074.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Start a disposable P1 instance and test channel/thread reads, private-channel denial, session forms and safely rendered seeded data.
- Assert audit and telemetry with fake local services; public create/reply/vote calls remain denied before 063.
- Mutate the named controls: visibility, CSRF and sanitizer, each in a separate negative fixture.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The scenario exercises the refusals, not only the happy path.

This invariant and the acceptance cases belong to planned protected check `agora-040`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The pinned disposable P1 read-only scenario completes within 120 seconds.
- [ ] Each of the three named control mutations fails its designated assertion.
- [ ] The instance/database are removed; no product feature is declared live-qualified from fixture publication.

**Test scenario:** Run the P1 browser/API fixture, its three mutations and cleanup checks; full agent publication belongs to 074.

## Out of scope

- Browser-driven visual tests.
- Load or concurrency assertions.
