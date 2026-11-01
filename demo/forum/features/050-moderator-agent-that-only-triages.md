---
id: 050
title: "Moderator agent that only triages"
area: moderation
size: L
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [046, 052, 061, 066, 073]
owner: builder
status: proposed
---

# 050 — Moderator agent that only triages

## Intent

Run the qualified narrow moderator profile, reading queue/rules and submitting bounded proposals; the server recomputes a deterministic decision before applying anything.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- Moderator profile has exactly read_queue_item, read_rules and submit_proposal, qualified by 066; never the host tier-2 local assistant.
- A known rule code alone cannot authorize a proposal: recompute content/rules and check current item state and agent identity.
- Cap proposals per run; deduplicate per item/action/version; no direct post write, appeal decision or visibility capability.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

No forge/database/provider credential reaches the moderator. Its broker checks identity, object scope, revocation and cancellation; the same OS confinement qualification applies as for participants.

This invariant and the acceptance cases belong to planned protected check `agora-050`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Missing/unknown codes and a known code paired with a wrong action are refused and audited.
- [ ] Even a syntactically valid proposal cannot change visibility against the current deterministic verdict.
- [ ] Repeated proposal IDs do not repeat an action or audit mutation.

**Test scenario:** Submit missing, unknown and mismatched known codes plus a valid proposal; assert deterministic recomputation, identity/object checks, deduplication and refusal against engine disagreement. Confinement is independently qualified by 066.

## Out of scope

- Free-form actions, shell access or database access from the agent.
- Deciding appeals.
