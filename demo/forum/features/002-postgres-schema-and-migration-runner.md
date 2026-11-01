---
id: 002
title: "Postgres schema and migration runner"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 002 — Postgres schema and migration runner

## Intent

Make Postgres the only store, with versioned SQL migrations applied by an idempotent runner that holds an advisory lock and refuses a schema newer than the code.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- `migrations/` with numbered SQL files and a `schema_migrations` table.
- A `migrate` command that acquires an advisory lock, applies pending files in one transaction each, and reports what it did.
- A refusal when the database records a version the checkout does not contain.
- Initialize a trusted migration entrypoint; schema-changing features add numbered migrations inside product/migrations/ and always require owner review. Bootstrap also disables live content admission until the complete qualified pipeline is present.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Connection parameters come from the environment and are never echoed; a non-local host must present TLS or the runner refuses.

This invariant and the acceptance cases belong to planned protected check `agora-002`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two consecutive runs apply nothing the second time and exit 0.
- [ ] A migration that raises leaves no partial DDL behind.
- [ ] A database ahead of the checkout stops the command with a downgrade-is-required message.

**Test scenario:** Apply to an ephemeral Postgres twice; then inject a failing migration and assert the schema is unchanged.

## Out of scope

- An ORM or a second storage engine.
- Data migrations or backfills beyond schema changes.
