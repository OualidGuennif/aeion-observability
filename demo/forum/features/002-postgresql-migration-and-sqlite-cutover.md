---
id: 002
sequence: 2
title: "PostgreSQL migration and SQLite cutover"
area: foundation
size: L
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [001]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 002 — PostgreSQL migration and SQLite cutover

## Intent

Migrate the existing Quarkus product from SQLite to PostgreSQL with one versioned migration history and a verified data-preserving cutover; keep the original SQLite volume available for rollback.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Introduce the PostgreSQL driver and versioned schema on a disposable database.
2. Add a bounded import from an immutable SQLite backup and compare integrity.
3. Prove backup/restore and rollback conditions before proposing a live cutover.

**Scope:**

- Use the Quarkus PostgreSQL JDBC integration and Flyway versioned SQL under demo/forum-app/src/main/resources/db/migration/; retain Hibernate with schema generation disabled.
- Replace the custom SQLite migration runner only after matching schema/version/checksum and concurrent migration-lock tests; never maintain two active migration authorities.
- An operator-only bounded migration job reads an immutable SQLite backup, imports into a fresh PostgreSQL database and validates IDs, relations, UTC timestamps, normalized content, accounts/sessions and the audit chain. It never prints sensitive fields.
- Pin the PostgreSQL image, separate migration-owner and application roles, local-only database transport and documented TLS policy. Production startup refuses missing or incompatible schema.
- Cut over only after counts, deterministic integrity checks and a disposable PostgreSQL backup/restore pass. Quiesce writes, record the boundary and retain the original volume unchanged; rollback cannot discard post-cutover writes silently.
- Product Compose/runbook changes are reviewed artifacts; no automatic deployment, database deletion or destructive migration is authorized by generating the artifact.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Migration credentials exist only in the isolated operator job. The application has least-privilege PostgreSQL grants. Never log connection strings, hashes, passwords or imported data. Remote database connections require certificate and hostname verification; only an explicitly isolated local development transport may omit TLS.

This invariant and the acceptance cases belong to planned protected check `agora-002`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Against a disposable PostgreSQL instance, applying migrations twice is idempotent; competing runners serialize and altered checksums or a schema newer than the code are refused.
- [ ] A failing transactional migration leaves no partial schema; the application role cannot perform schema DDL or modify audit history.
- [ ] An existing SQLite fixture migrates with matching row counts, stable identifiers, timestamps, normalized content and verifiable audit chain; duplicate/replayed import cannot duplicate rows.
- [ ] Backup then restore to a second disposable PostgreSQL instance reproduces counts and integrity checks; failed validation blocks cutover and leaves the SQLite source untouched.
- [ ] After the switch the Quarkus suite uses PostgreSQL; SQLite dependencies/configuration and the active SQLite service are removed without deleting its preserved data volume.

**Test scenario:** Run protected migration, concurrent-start, failing-DDL, checksum/ahead-schema, SQLite-import, replay and PostgreSQL restore fixtures; prove a deliberately altered imported row blocks cutover.

## Out of scope

- Migrating the factory SQLite queue or observability databases.
- Automatic destructive DDL, dropping the old volume or rolling back by losing committed writes.
