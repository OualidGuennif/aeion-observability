---
id: 100
title: "Backups and a restore drill"
area: ops
size: M
parallel: false
depends_on: [099]
owner: builder
status: proposed
---

# 100 — Backups and a restore drill

**Goal.** Back up Postgres, the audit chain and the Langfuse store daily, and prove a restore in a script that runs the drill, not a paragraph that promises it.

## Scope

- A daily dump with a retention window and a checksum.
- A drill that restores into a scratch volume and verifies row counts and the audit chain.
- An alert line when a backup is missing or the drill fails.

## Out of scope

- Off-site replication to a cloud provider.
- Point-in-time recovery beyond the daily dump.

## Acceptance

- [ ] The drill restores the dump and verifies the audit chain end to end.
- [ ] A truncated dump makes the drill fail loudly.
- [ ] The retention window deletes only files past its age.

## Security

Backups are encrypted at rest and readable only by the deploy user; the drill never touches the live database.

## Test

Run the drill against fixtures, including a corrupted dump.
