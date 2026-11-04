---
id: 070
sequence: 68
title: "Thread summaries in Hindsight"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [069, 022, 096]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 070 — Thread summaries in Hindsight

## Intent

Retain one deterministic public-thread category/count/outcome summary in Hindsight, with stable identity, deletion and retention; no body analysis or model call is needed.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Build deterministic public metadata summaries without reading bodies.
2. Retain by thread/version with bounded retention through trusted Hindsight.
3. Replay closure/deletion events and prove idempotency plus visibility removal.

**Scope:**

- On thread closure, a trusted background operation creates one deterministic summary of public category/count/outcome metadata, without reading bodies.
- Store a stable thread/version key, bounded codes/counts and a retention deadline in the demo synthetic namespace.
- Delete or update records idempotently when public visibility changes; private thread content/identity is never retained.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Summaries derive only from authorized public metadata counts and codes, without reading thread text. Trusted integration owns retention/deletion; recalled data never grants authority.

This invariant and the acceptance cases belong to planned protected check `agora-070`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Repeated close notifications retain one record per public thread/version.
- [ ] The record has only allowlisted codes/counts/opaque IDs, no handles or body excerpts of any length.
- [ ] Deletion or loss of visibility removes the corresponding record by the next bounded background run.

**Test scenario:** Deliver repeated close/delete/visibility events; assert idempotent records, exact metadata schema, retention and removal without body/handle fields.

## Out of scope

- Semantic search in the product UI.
- Summarizing held content.
