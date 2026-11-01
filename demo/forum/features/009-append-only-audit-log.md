---
id: 009
title: "Append-only audit log"
area: foundation
size: M
parallel: false
depends_on: [002]
owner: builder
status: proposed
---

# 009 — Append-only audit log

**Goal.** Record every privileged action in a hash-chained table with a verifier, so tampering with history is detectable without trusting the application.

## Scope

- `audit` table with sequence, actor, action code, target, outcome, previous hash and entry hash.
- A single write path that refuses updates and deletes at the database role level.
- A `verify` command that walks the chain and reports the first break.

## Out of scope

- Log shipping to a third party.
- Content capture: audit records codes and identifiers, not text.

## Acceptance

- [ ] Editing one row makes `verify` fail at that sequence.
- [ ] A failed action is audited with its outcome, not dropped.
- [ ] The chain survives a restart.

## Security

The application role cannot UPDATE or DELETE the table; only INSERT is granted.

## Test

Write a known sequence, tamper with a row out of band and assert `verify` names it.
