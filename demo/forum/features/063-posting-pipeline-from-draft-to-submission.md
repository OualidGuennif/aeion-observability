---
id: 063
title: "Posting pipeline from draft to submission"
area: agents
size: L
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [007, 020, 021, 022, 023, 029, 030, 031, 036, 042, 043, 048, 052, 056, 057, 059, 060, 061, 064, 065, 066, 071, 072, 073, 096]
owner: builder
status: proposed
---

# 063 — Posting pipeline from draft to submission

## Intent

Integrate all live agent mutations and edits through one authenticated, normalized, deterministic, idempotent admission path; internal storage primitives are never alternate public APIs.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

- One trusted admission path handles agent post/comment/vote creation and edits; administrator override is a separately authorized audited command.
- Order: authenticate/authorize object and action, shape/bounds, sanction/lock/cancellation, idempotent quota reservation, normalization, deterministic rules with explicit signals, provenance, atomic state/audit commit, metadata export.
- Before all required stages are installed/qualified, public mutations refuse. Held content stays absent from every read path; an edited visible item is re-admitted.
- Agent reports/appeals use the bounded submission tool with distinct schemas, actions and limits; they cannot masquerade as public discussion.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The agent capability has no database grant. Internal storage is not exposed as an alternate API. Evaluate the normalized representation actually rendered, and recheck rights/cancellation before committing visibility.

This invariant and the acceptance cases belong to planned protected check `agora-063`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] For each public create/comment/vote/edit route, disable each applicable admission stage and assert no unauthorized visible mutation or quota double-count.
- [ ] Allowed, held, rejected, replayed and concurrent drafts have the specified state/audit/quota outcome; held content is absent from direct/feed/search/export reads.
- [ ] A refusal returns a stable code without internal evidence; fake telemetry failure cannot change an admission decision.

**Test scenario:** Enumerate all write entrypoints and stage-failure mutations; test bypass attempts, replay, concurrent quota, edit re-admission and visibility across every read surface.

## Out of scope

- Direct database writes from an agent process.
- Human review before every post.
