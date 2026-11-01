---
id: 004
title: "Accounts and password hashing"
area: foundation
size: M
parallel: false
depends_on: [002]
owner: builder
status: proposed
---

# 004 — Accounts and password hashing

**Goal.** Add human accounts with argon2id hashes, a unique handle and a disabled-by-default state, so access exists before any route needs it.

## Scope

- `accounts` table with handle, hash, role placeholder, disabled flag and timestamps.
- Create, verify and disable operations with constant-time comparison.
- A CLI command to create the first administrator.

## Out of scope

- Registration, password reset or email.
- Agent accounts, which are tokens, not passwords.

## Acceptance

- [ ] Two accounts cannot share a handle, including by case.
- [ ] A wrong password costs the same time as an unknown handle.
- [ ] A disabled account cannot verify even with the right password.

## Security

Argon2id with the library's current recommended parameters; hashes never leave the process and never appear in logs.

## Test

Create an account, verify the right and wrong password, disable it and assert refusal; assert the handle uniqueness race ends in one failure.
