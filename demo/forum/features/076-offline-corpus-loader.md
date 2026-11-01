---
id: 076
title: "Offline corpus loader"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [075, 002, 009]
owner: builder
status: proposed
---

# 076 — Offline corpus loader

## Intent

Load regular local corpus files in an offline job with only an explicit local Postgres transport; arbitrary internet/DNS egress remains denied.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- A trusted offline job reads regular JSON files from one confined drop root and writes Postgres idempotently.
- Use per-item checksums and transactional outcomes; run in a network-denied namespace permitting only the explicitly configured local database transport.
- No internet/DNS/default route or arbitrary client is available; test real outbound refusals rather than imports alone.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Deny general egress at OS policy; a fixed local database capability is the only required transport. Absence of an HTTP import is not isolation evidence.

This invariant and the acceptance cases belong to planned protected check `agora-076`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
