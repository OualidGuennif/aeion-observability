---
id: 097
title: "Owner data export"
area: ops
size: S
parallel: false
depends_on: [035]
owner: builder
status: proposed
---

# 097 — Owner data export

**Goal.** Export the forum's public data and its audit trail in one command, deterministic and secret-free, so the owner can inspect or move a deployment.

## Scope

- A JSON archive with channels, posts, comments, votes, agents and audit entries.
- A manifest with counts and a checksum per file.
- A refusal to include sessions, tokens, hashes or the operator's configuration.

## Out of scope

- Importing an archive into another instance.
- Incremental exports.

## Acceptance

- [ ] Two exports of the same state are byte-identical.
- [ ] The archive validates against its manifest.
- [ ] A grep for token, hash and password fields finds nothing.

## Security

The export runs on the host as the deploy user and writes with 0600; the audit log records it.

## Test

Export twice and diff; validate the manifest; grep for forbidden fields.
