---
id: 076
sequence: 78
title: "Offline corpus loader"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [075, 002, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 076 — Offline corpus loader

## Intent

Load regular local corpus files in an offline job with only an explicit local Postgres transport; arbitrary internet/DNS egress remains denied.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Read bounded regular corpus files from one confined local root.
2. Import by stable ID/checksum into PostgreSQL transactionally.
3. Replay imports and prove traversal/symlink and actual network-policy refusals.

**Scope:**

- A trusted offline job reads regular JSON files from one confined drop root and writes Postgres idempotently.
- Use per-item checksums and transactional outcomes; run in a network-denied namespace permitting only the explicitly configured local database transport.
- No internet/DNS/default route or arbitrary client is available; test real outbound refusals rather than imports alone.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Deny general egress at OS policy; a fixed local database capability is the only required transport. Absence of an HTTP import is not isolation evidence.

This invariant and the acceptance cases belong to planned protected check `agora-076`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Loading twice leaves identical data and count; repeated checksums do not duplicate records.
- [ ] A malformed file is reported/skipped atomically; symlink/traversal files are refused.
- [ ] Actual internet/DNS connection attempts fail while the permitted local database connection works.

**Test scenario:** Load twice and inject malformed/symlink files; test real network-denial policy plus the permitted local DB connection. An import scan alone cannot qualify isolation.

## Out of scope

- RSS, scrapers or any remote fetch.
- Scheduling through a cloud service.
