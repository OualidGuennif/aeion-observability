---
id: 047
title: "Appeals"
area: moderation
size: M
parallel: false
depends_on: [046]
owner: builder
status: proposed
---

# 047 — Appeals

**Goal.** Let an author appeal a decision once, with the reason code attached, and require a different moderator to decide, so a decision is checked rather than repeated.

## Scope

- `appeals` table linked to one moderation action and one author.
- A rule that the deciding moderator differs from the original one.
- Outcomes: upheld, overturned, or escalated to the administrator.

## Out of scope

- Appeals against bans by non-authors.
- Multiple appeal rounds on the same action.

## Acceptance

- [ ] A second appeal on the same action answers 409.
- [ ] The original moderator cannot decide the appeal.
- [ ] An overturned appeal restores the content in the same transaction.

## Security

Appeals are rate limited per author and audited like any other action.

## Test

File two appeals, attempt self-review, then overturn and assert visibility restored.
