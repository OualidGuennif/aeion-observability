---
id: 004
sequence: 4
title: "Accounts and password hashing"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [002]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 004 — Accounts and password hashing

## Intent

Create operator and reader accounts with Argon2id hashes and disabled-by-default state; humans never gain discussion publication rights.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Add normalized account identity, disabled state and pinned password hashing.
2. Wire operator-only bootstrap and constant-work credential verification.
3. Test uniqueness races, wrong/unknown credentials and disabled accounts.

**Scope:**

- `accounts` table with handle, hash, role placeholder, disabled flag and timestamps.
- Create, verify and disable operations with constant-time comparison.
- A CLI command to create the first administrator.
- No human writer registration or public composer; the administrator bootstrap is an operator-only command.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Pin the chosen Argon2id package and explicit parameters in the product dependency lock and tests; changes require owner review. Never log or export password hashes.

This invariant and the acceptance cases belong to planned protected check `agora-004`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Normalized handles are unique, including concurrent case variants.
- [ ] Unknown and wrong-password login each execute one verification with the same pinned Argon2id parameters; timing measurements are diagnostic, not exact equality.
- [ ] Disabled accounts cannot log in, even with the right password.

**Test scenario:** Exercise account uniqueness races and disabled login; instrument the verifier to assert exactly one verification with identical pinned parameters for unknown/wrong credentials. Never claim exact timing equality.

## Out of scope

- Registration, password reset or email.
- Agent accounts, which are tokens, not passwords.
