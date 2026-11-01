---
id: 001
title: "App skeleton and settings"
area: foundation
size: S
parallel: false
depends_on: []
owner: builder
status: proposed
---

# 001 — App skeleton and settings

**Goal.** Create the FastAPI application factory, a typed settings object read from the environment, and `/healthz`, so every later feature boots, configures and probes the app in one place.

## Scope

- Application factory with explicit router registration and no import-time side effects.
- Settings object with defaults, ranges and a fail-closed check for anything required.
- `GET /healthz` returning liveness only.

## Out of scope

- Any forum route, database access or authentication.
- A settings admin page or a configuration file format.

## Acceptance

- [ ] The server answers 200 on `/healthz` with only the environment variables the spec names.
- [ ] A missing required setting stops the process with one message naming the key, never its value.
- [ ] An unknown environment variable is ignored, not silently mapped.

## Security

Settings are never logged or rendered; the health endpoint exposes liveness, not build or host details.

## Test

Start the app with a minimal environment and assert 200; remove a required setting and assert a clean startup failure.
