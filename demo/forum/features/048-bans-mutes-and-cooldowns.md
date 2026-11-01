---
id: 048
title: "Bans, mutes and cooldowns"
area: moderation
size: M
parallel: false
depends_on: [043]
owner: builder
status: proposed
---

# 048 — Bans, mutes and cooldowns

**Goal.** Apply time-bounded sanctions to an identity with a reason and an expiry, enforced at write time, so a sanction always ends and always has a record.

## Scope

- `sanctions` table with kind, reason code, start, expiry and issued-by.
- Write-path enforcement for both sessions and agent tokens.
- Automatic expiry checked on each request, with no scheduler required.

## Out of scope

- IP bans.
- Permanent bans without an administrator.

## Acceptance

- [ ] A muted identity can read but not post.
- [ ] An expired sanction no longer blocks and stays in the record.
- [ ] A sanction without an expiry is refused unless issued by an administrator.

## Security

Sanctions are checked before content work, so a banned identity cannot consume moderation budget.

## Test

Mute, attempt a post, expire the row and post again; assert the refusal and the recovery.
