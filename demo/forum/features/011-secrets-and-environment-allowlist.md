---
id: 011
title: "Secrets and environment allowlist"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [001]
owner: builder
status: proposed
---

# 011 — Secrets and environment allowlist

## Intent

Read configuration only from an explicit allowlist of environment keys, refuse weak or missing secrets, and never hand the full environment to a child process.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- An allowlist mapping name to type and required flag.
- A startup check that rejects a default, short or placeholder secret.
- A child-process environment builder that passes only the keys a run needs.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

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
