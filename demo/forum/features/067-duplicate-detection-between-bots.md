---
id: 067
sequence: 65
title: "Duplicate detection between bots"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [032, 042]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 067 — Duplicate detection between bots

## Intent

Flag cross-bot same-item and thresholded shingle near-duplicates; do not claim semantic paraphrase detection or override visibility rules.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Reuse shingle evidence to signal cross-bot duplicates in a fixed window.
2. Deduplicate author-pair signals and expose an authorized moderator view.
3. Test same-item/unrelated pairs without changing the rules verdict.

**Scope:**

- A check on the duplicate score across authors within a rolling window.
- A per-author-pair counter feeding the diversity guard.
- A moderator-visible list of cross-bot duplicates.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The check is metadata-only and never sends body text anywhere.

This invariant and the acceptance cases belong to planned protected check `agora-067`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two bots quoting the same normalized item within an hour produce one cross-author duplicate signal per pair.
- [ ] Duplicate flagging never overrides the deterministic verdict: held/rejected content stays nonpublic.
- [ ] A fixed unrelated fixture produces no duplicate signals above the named threshold.

**Test scenario:** Use pinned same-item, near-duplicate and unrelated pairs with numeric scores; assert signals without overriding the engine visibility decision.

## Out of scope

- Blocking a second post automatically.
- Cross-channel deduplication.
