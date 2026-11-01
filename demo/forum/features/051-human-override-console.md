---
id: 051
title: "Human override console"
area: moderation
size: M
parallel: false
depends_on: [046]
owner: builder
status: proposed
---

# 051 — Human override console

**Goal.** Let the administrator overturn any moderation action from one page, with a mandatory justification, so a wrong automated decision is one click from repair.

## Scope

- A console listing recent actions with their evidence and a restore control.
- A mandatory free-text justification stored with the override.
- A confirmation step and a limit on overrides per minute.

## Out of scope

- Editing audit rows.
- Overriding the audit chain itself.

## Acceptance

- [ ] An override restores visibility and appends an audit entry citing the original action.
- [ ] An override without justification is refused.
- [ ] The console is unreachable for non-administrators, including by url.

## Security

The console requires a fresh session, and every view is audited.

## Test

Override a hold, assert restoration and audit; attempt the console as moderator and assert 403.
