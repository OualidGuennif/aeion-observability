---
id: 092
title: "Public edit history"
area: forum
size: M
parallel: false
depends_on: [030]
owner: builder
status: proposed
---

# 092 — Public edit history

**Goal.** Show that a post was edited and when, with the number of revisions, while keeping the diffs for moderators only.

## Scope

- A revision count and last-edit time rendered next to the author.
- A moderator view with the rendered diff per revision.
- A refusal to hide an edit by deleting the revision rows.

## Out of scope

- Public diffs.
- Editing after a moderation action.

## Acceptance

- [ ] An edited post states the number of revisions and the time.
- [ ] An unedited post shows no marker.
- [ ] The revision rows survive a post deletion as tombstones.

## Security

Revisions are append-only; the audit chain records each edit.

## Test

Edit twice and delete; assert the marker, the moderator diffs and the surviving rows.
