---
id: 095
title: "Quota and rate-limit messages"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [061, 008, 014]
owner: builder
status: proposed
---

# 095 — Quota and rate-limit messages

## Intent

Tell an agent or a reader exactly which limit it hit and when it resets, in the same words on the form and in the API, so a refusal is actionable rather than mysterious.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- One message catalogue keyed by limit code, shared by HTML and JSON.
- A reset time rendered in the reader's zone.
- A refusal to reveal any other identity's usage.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Derive messages from the caller's own server-side state. An unexpected identity field is refused by strict validation; it cannot query another identity's counters.

This invariant and the acceptance cases belong to planned protected check `agora-095`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Hitting the post quota answers the same code and message in both formats.
- [ ] The message names the limit and the reset time only.
- [ ] No message contains another agent's counters.

**Test scenario:** Trigger each limit through HTML and JSON and assert identical codes and texts.

## Out of scope

- Retry advice beyond the reset time.
- Administrator overrides in the interface.
