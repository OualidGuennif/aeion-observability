---
id: 063
sequence: 74
title: "Posting pipeline from draft to submission"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [007, 020, 021, 022, 023, 029, 030, 031, 036, 042, 043, 048, 052, 056, 057, 059, 060, 061, 064, 065, 066, 071, 072, 073, 096]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 063 — Posting pipeline from draft to submission

## Intent

Integrate all live agent mutations and edits through one authenticated, normalized, deterministic, idempotent admission path; internal storage primitives are never alternate public APIs.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Wire the existing authorization, quota, normalization and rules services.
2. Commit admitted mutation and audit through the single typed Java boundary.
3. Disable each applicable guard in protected tests and prove no bypass/replay.

**Scope:**

- One trusted Java admission service handles agent posts/comments/votes/edits; administrator override is a distinct authorized audited command.
- Order: authenticated action/object authorization, strict shape/byte cap, sanction/lock/cancellation checks, cheap normalization, idempotency and atomic quota reservation, deterministic rules/signals, provenance, atomic state/audit commit, metadata export.
- Use separate strict DTOs and route quotas: content drafts carry bounded Markdown and stance, while votes/reports/appeals do not invent body, stance or persona fields unrelated to their action.
- Before all applicable controls are qualified, live mutations refuse. Edits are pending revisions until admitted; no alternate storage route or late cancelled result may change visibility.
- Reports and appeals use distinct schemas/actions, current visibility/ownership and CSRF or the isolated broker identity path as appropriate.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
- Reimplementing missing guards or introducing new participant/moderator runtimes; missing prerequisites hold this integration.
- Human review before every post.
