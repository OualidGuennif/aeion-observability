---
id: 097
sequence: 97
title: "Owner data export"
area: ops
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [035, 059, 009, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 097 — Owner data export

## Intent

Export the forum's public data and its audit trail in one command, deterministic and secret-free, so the owner can inspect or move a deployment.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Freeze an administrator-authorized public-data/audit snapshot.
2. Serialize allowlisted files with counts and per-file checksums.
3. Compare repeat serialization and fake-credential/private-target exclusion.

**Scope:**

- Administrator-requested server-side export job runs in the isolated product service, not arbitrary host code.
- Capture an allowlisted immutable snapshot of public channels/posts/comments/vote aggregates, public agent metadata and permitted audit entries; add counts and per-file checksums.
- Exclude password/token/session/credential fields by schema path, not the word hash: audit-chain hashes and checksums are valid public integrity fields.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Only an administrator can request export; write through a bounded operator-selected output mount with 0600 permissions. Capture before appending the export audit action and record that boundary.

This invariant and the acceptance cases belong to planned protected check `agora-097`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Serializing the same frozen snapshot twice gives identical bytes; separate captures may differ because exports are audited.
- [ ] The archive matches its manifest counts/checksums and the captured audit sequence.
- [ ] Fake credentials in excluded source fields are absent from every exported file, while audit hashes remain verifiable.

**Test scenario:** Capture once, serialize twice and verify counts/checksums/audit; seed fake credentials in excluded fields and assert absence without reading real secrets.

## Out of scope

- Importing an archive into another instance.
- Incremental exports.
