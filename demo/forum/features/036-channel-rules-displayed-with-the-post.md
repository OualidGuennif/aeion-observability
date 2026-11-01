---
id: 036
title: "Channel rules displayed with the post"
area: forum
size: S
parallel: false
depends_on: [019]
owner: builder
status: proposed
---

# 036 — Channel rules displayed with the post

**Goal.** Show the rules a post was judged under, linked to their version, so a moderation decision is explainable to the reader and to an appeal.

## Scope

- A rules version recorded with every post at creation.
- A rules page per channel rendering the version in force.
- A link from a held post to the exact rule that held it.

## Out of scope

- Per-user rule acceptance.
- Rule editing in the interface.

## Acceptance

- [ ] A post held under version 2 cites rule 2 in the moderation note.
- [ ] Changing the rules later does not rewrite the citation on old posts.
- [ ] The rules page is readable without authentication.

## Security

Rules are data with a version and a hash; a change is a reviewed commit, not a database edit.

## Test

Post under two rule versions and assert each post cites its own version.
