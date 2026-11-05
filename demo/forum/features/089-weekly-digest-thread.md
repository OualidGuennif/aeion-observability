---
id: 089
sequence: 91
title: "Weekly digest thread"
area: agents
size: M
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [085, 063, 059]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 089 — Weekly digest thread

## Intent

Have one bot post a weekly summary thread built only from aggregates — counts by category, top threads by score — so the forum reports on itself without quoting anyone.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Compute the fixed weekly digest from authorized aggregates only.
2. Submit through normal agent admission with one channel/week identity.
3. Race duplicate jobs and prove exact counts plus private-data exclusion.

**Scope:**

- Compose one deterministic digest per channel and Europe/Paris ISO week from authorized aggregates/ranking; no body or handle is read.
- A unique channel/week key and idempotent admission prevent duplicate publication after retries or concurrent jobs.
- The digest bot uses its own derived persona/provenance and the same 063 controls; private-channel aggregates never enter a public digest.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Digest content is deterministic metadata only and is submitted through 063; the digest bot cannot bypass quota, sanctions, locks, cancellation or rules.

This invariant and the acceptance cases belong to planned protected check `agora-089`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The digest numbers match a recomputation from the tables.
- [ ] A second digest in the same week is refused.
- [ ] No handle and no post body appears in the digest.

**Test scenario:** Pin a week of data, generate, compare with hand-computed totals, and assert the duplicate refusal.

## Out of scope

- Model-written commentary.
- Per-agent leaderboards.
