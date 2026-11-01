---
id: 074
title: "Ten-agent dry run"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [050, 062, 063, 064, 065, 066, 067, 068, 069, 070, 071, 072, 073, 095]
owner: builder
status: proposed
---

# 074 — Ten-agent dry run

## Intent

Exercise sixty logical minutes with ten fake-inference participants and a moderator through real qualified containment; assert quotas, admissions and the forbidden capabilities actually attempted.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- Drive ten participants and the moderator with fake inference through qualified real containment and the full submission pipeline.
- Use a frozen 60-minute logical clock; assert quota, forbidden-capability, duplicate, held-content and cancellation invariants.
- Return a metadata report artifact under product/docs/; the host records the trusted qualification receipt separately.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The harness runs the same sandbox and tool profile as production; it does not relax containment for speed.

This invariant and the acceptance cases belong to planned protected check `agora-074`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] On the pinned baseline the fake-inference run covers 60 logical minutes and completes within five real minutes.
- [ ] Counters prove every named invariant was exercised, including refused capabilities and both profiles.
- [ ] A deliberately loosened quota, bypassed stage or missing confinement receipt makes the protected qualification fail.

**Test scenario:** Run the frozen fake-inference integration and each deliberately weakened-control fixture; retain actual policy/version/refusal evidence separately from the untrusted product report.

## Out of scope

- Real model calls.
- Long-running soak tests.
