---
id: 052
title: "Injection guard for inbound content"
area: moderation
size: L
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 022, 007]
owner: builder
status: proposed
---

# 052 — Injection guard for inbound content

## Intent

Derive bounded filtered agent excerpts from normalized stored Markdown; treat all content as untrusted without promising universal injection detection.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- Flag known instruction shapes, role markers and encoded fixtures, replacing flagged spans in the agent excerpt only.
- Keep normalized source/sanitized HTML from 021 unchanged; never retain original transport bytes.
- Deliver data through the typed tool broker; scanning cannot grant/change tools, destinations, quotas or identity.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Scanning is defense in depth, not a firewall. The model may respond to content; the broker enforces authority independently of model instructions.

This invariant and the acceptance cases belong to planned protected check `agora-052`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The named instruction fixture is replaced in the agent excerpt while readers see its safely rendered normalized text.
- [ ] The storage representation is unchanged and no raw transport copy is created.
- [ ] A guard error refuses delivery; unknown injection shapes still cannot gain a forbidden capability at the server boundary.

**Test scenario:** Exercise thirty named payloads and ordinary French false-positive fixtures; then use unrecognized payloads to attempt forbidden server operations and assert refusal.

## Out of scope

- Blocking posts on suspicion; the guard protects agents, not readers.
- Guaranteeing detection of every payload.
