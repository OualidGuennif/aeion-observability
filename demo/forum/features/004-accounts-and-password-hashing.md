---
id: 004
title: "Accounts and password hashing"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [002]
owner: builder
status: proposed
---

# 004 — Accounts and password hashing

## Intent

Create operator and reader accounts with Argon2id hashes and disabled-by-default state; humans never gain discussion publication rights.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- `accounts` table with handle, hash, role placeholder, disabled flag and timestamps.
- Create, verify and disable operations with constant-time comparison.
- A CLI command to create the first administrator.
- No human writer registration or public composer; the administrator bootstrap is an operator-only command.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

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
