---
id: 002
title: "Postgres schema and migration runner"
area: foundation
size: M
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 002 — Postgres schema and migration runner

**Goal.** Make Postgres the only store, with versioned SQL migrations applied by an idempotent runner that holds an advisory lock and refuses a schema newer than the code.

## Scope

- `migrations/` with numbered SQL files and a `schema_migrations` table.
- A `migrate` command that acquires an advisory lock, applies pending files in one transaction each, and reports what it did.
- A refusal when the database records a version the checkout does not contain.

## Out of scope

- An ORM or a second storage engine.
- Data migrations or backfills beyond schema changes.

## Acceptance

- [ ] Two consecutive runs apply nothing the second time and exit 0.
- [ ] A migration that raises leaves no partial DDL behind.
- [ ] A database ahead of the checkout stops the command with a downgrade-is-required message.

## Security

Connection parameters come from the environment and are never echoed; a non-local host must present TLS or the runner refuses.

## Test

Apply to an ephemeral Postgres twice; then inject a failing migration and assert the schema is unchanged.
