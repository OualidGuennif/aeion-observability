---
id: 011
title: "Secrets and environment allowlist"
area: foundation
size: S
parallel: false
depends_on: [001]
owner: builder
status: proposed
---

# 011 — Secrets and environment allowlist

**Goal.** Read configuration only from an explicit allowlist of environment keys, refuse weak or missing secrets, and never hand the full environment to a child process.

## Scope

- An allowlist mapping name to type and required flag.
- A startup check that rejects a default, short or placeholder secret.
- A child-process environment builder that passes only the keys a run needs.

## Out of scope

- A secrets manager integration.
- Rotating secrets at runtime.

## Acceptance

- [ ] A placeholder secret stops the process with the key name only.
- [ ] A child process sees only its allowlisted keys.
- [ ] An unexpected key in the environment is ignored and never logged.

## Security

The allowlist is the only route from the host environment into the application and its children.

## Test

Start with a weak secret and assert refusal; spawn a child and assert its environment keys.
