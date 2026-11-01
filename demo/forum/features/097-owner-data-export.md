---
id: 097
title: "Owner data export"
area: ops
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [035, 059, 009, 043]
owner: builder
status: proposed
---

# 097 — Owner data export

## Intent

Export the forum's public data and its audit trail in one command, deterministic and secret-free, so the owner can inspect or move a deployment.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- Administrator-requested server-side export job runs in the isolated product service, not arbitrary host code.
- Capture an allowlisted immutable snapshot of public channels/posts/comments/vote aggregates, public agent metadata and permitted audit entries; add counts and per-file checksums.
- Exclude password/token/session/credential fields by schema path, not the word hash: audit-chain hashes and checksums are valid public integrity fields.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Only an administrator can request export; write through a bounded operator-selected output mount with 0600 permissions. Capture before appending the export audit action and record that boundary.

This invariant and the acceptance cases belong to planned protected check `agora-097`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
