---
id: 030
title: "Author edit window and tombstones"
area: forum
size: M
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 030 — Author edit window and tombstones

**Goal.** Let an author fix a post within a short window and leave a tombstone afterwards, so history stays legible and quiet deletion is impossible.

## Scope

- A fifteen-minute edit window with a revision record per edit.
- Deletion replaced by a tombstone keeping the thread structure.
- A revision list visible to moderators only.

## Out of scope

- Restoring a deleted post from the interface.
- Editing after a moderation action.

## Acceptance

- [ ] An edit after the window answers 409 and changes nothing.
- [ ] A deleted post keeps its replies and shows a tombstone.
- [ ] Each edit stores the previous rendered body.

## Security

Revisions are append-only; the audit chain covers deletions and edits.

## Test

Edit inside and after the window, delete a parent and assert the tombstone and the revision rows.
