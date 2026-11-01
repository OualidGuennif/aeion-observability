---
id: 001
title: "App skeleton and settings"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: []
owner: builder
status: proposed
---

# 001 — App skeleton and settings

## Intent

Create the FastAPI application factory, a typed settings object read from the environment, and `/healthz`, so every later feature boots, configures and probes the app in one place.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- Application factory with explicit router registration and no import-time side effects.
- Settings object with defaults, ranges and a fail-closed check for anything required.
- `GET /healthz` returning liveness only.
- Settings: AGORA_SESSION_SECRET required (at least 32 bytes); AGORA_DATABASE_URL optional until DB features; AGORA_TIMEZONE defaults to Europe/Paris; request body cap 16384 bytes, text cap 4000 codepoints, rendered cap 32768 bytes; invalid ranges fail startup.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

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

- Any forum route, database access or authentication.
- A settings admin page or a configuration file format.
