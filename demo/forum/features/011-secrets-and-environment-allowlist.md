---
id: 011
sequence: 11
title: "Secrets and environment allowlist"
area: foundation
size: S
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

# 011 — Secrets and environment allowlist

## Intent

Read configuration only from an explicit allowlist of environment keys, refuse weak or missing secrets, and never hand the full environment to a child process.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Define the configuration allowlist and reject weak required values.
2. Create minimal role-specific child environments at the trusted boundary.
3. Test ignored keys and synthetic canaries without reading real secrets.

**Scope:**

- An allowlist mapping name to type and required flag.
- A startup check that rejects a default, short or placeholder secret.
- A child-process environment builder that passes only the keys a run needs.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The allowlist is the only route from the host environment into the application and its children.

This invariant and the acceptance cases belong to planned protected check `agora-011`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A placeholder secret stops the process with the key name only.
- [ ] A child process sees only its allowlisted keys.
- [ ] An unexpected key in the environment is ignored and never logged.

**Test scenario:** Reject weak settings, inspect only a fake child environment, and use a synthetic credential canary in a denied host path during OS qualification; never inspect real secrets.

## Out of scope

- A secrets manager integration.
- Rotating secrets at runtime.
