---
id: 046
title: "Moderator actions"
area: moderation
size: M
parallel: false
depends_on: [042, 045]
owner: builder
status: proposed
---

# 046 — Moderator actions

**Goal.** Offer a small, audited action set — hold, approve, reject, lock, escalate — with a mandatory reason code, so every change of visibility is explainable.

## Scope

- Actions applied through one command that writes the state and the audit entry together.
- A mandatory rule code and an optional note per action.
- Idempotency: applying the same action twice is a no-op with a 200.

## Out of scope

- Bulk actions over a filter.
- Undo beyond an explicit restore action.

## Acceptance

- [ ] A hold removes the post from public reads within the same transaction.
- [ ] An action without a rule code is refused.
- [ ] A repeated action leaves one audit entry.

## Security

The state change and its audit row commit or roll back together.

## Test

Apply each action, repeat one, omit the code; assert state, visibility and audit rows.
