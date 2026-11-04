---
id: 001
sequence: 1
title: "App skeleton and settings"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: []
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 001 — App skeleton and settings

## Intent

Retain the Quarkus/Java application and Gradle build, with typed allowlisted configuration and GET /healthz; reuse the existing backend instead of introducing a second framework.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Reuse the Quarkus entrypoint and map only the documented configuration keys.
2. Add startup bounds and liveness without acquiring a database connection.
3. Prove minimal boot, missing-secret and invalid-bound refusals.

**Scope:**

- Explicit JAX-RS resources and CDI configuration using existing Quarkus conventions; no replacement backend or unrelated dependency upgrade.
- Typed configuration with bounded defaults and fail-closed startup checks for required values.
- GET /healthz is liveness only and must not acquire a database connection.
- AGORA_SESSION_SECRET is required (at least 32 bytes); PostgreSQL connection settings are required when database-backed features are enabled; Europe/Paris business timezone; request cap 16384 bytes, normalized text cap 4000 codepoints, rendered cap 32768 bytes. Invalid ranges refuse startup.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Settings are never logged or rendered; the health endpoint exposes liveness, not build or host details.

This invariant and the acceptance cases belong to planned protected check `agora-001`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] With only a non-placeholder 32-byte AGORA_SESSION_SECRET, GET /healthz returns 200 without opening a database connection.
- [ ] Removing AGORA_SESSION_SECRET stops startup naming only that key; invalid numeric bounds also refuse startup.
- [ ] An unknown environment variable is ignored and absent from logs and rendered pages.

**Test scenario:** Start the app with a minimal environment and assert 200; remove a required setting and assert a clean startup failure.

## Out of scope

- New forum behavior, database migration or authentication changes.
- FastAPI, Python application code or a second backend.
