---
id: 069
sequence: 67
title: "Bot memory checkpoint"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [059, 011]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 069 — Bot memory checkpoint

## Intent

Save a bounded identifiers-and-codes checkpoint per bot run through the trusted supervisor, without retaining bodies, free-text decisions or transcripts.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Define the identifiers/codes-only checkpoint and 4096-byte cap.
2. Write/read it through the trusted claude-mem integration.
3. Test round trip, dropped-ID counts and safe clean start on unavailability.

**Scope:**

- Trusted supervisor uses the explicit claude-mem API with platformSource pi; no memory credential reaches a bot.
- Checkpoint contains bounded thread IDs, draft IDs and refusal codes only, not free-text content or prompts.
- Pin a 4096-byte serialized cap and truncate oldest IDs first, recording dropped counts.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Checkpoint schema permits identifiers and refusal codes only; no free-text notes, body excerpts, provider keys or tool payloads.

This invariant and the acceptance cases belong to planned protected check `agora-069`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A second run reads the checkpoint written by the first.
- [ ] The checkpoint never exceeds the cap and records what was dropped.
- [ ] A missing checkpoint starts clean, never fails the run.

**Test scenario:** Write, read back and truncate; assert the round trip and the cap behaviour.

## Out of scope

- Long-term knowledge in claude-mem.
- Cross-bot memory sharing.
