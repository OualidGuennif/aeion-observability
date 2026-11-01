---
id: 100
title: "Community guidelines page"
area: ops
size: S
parallel: false
depends_on: [041]
owner: builder
status: proposed
---

# 100 — Community guidelines page

**Goal.** Publish the rules as a human-readable guide with one example per rule code, generated from the same file the engine uses, so readers and moderators read the same text.

## Scope

- A rendering of each rule code with its prose and one allowed and one refused example.
- A version stamp matching the machine rules.
- A link from a moderation note to the exact rule.

## Out of scope

- A commentable policy or a legal notice.
- Per-language versions.

## Acceptance

- [ ] Every rule code appears exactly once.
- [ ] The version stamp equals the rules hash in force.
- [ ] A moderation note's link opens the cited rule.

## Security

The guide is generated from the reviewed rules file; it has no write path.

## Test

Render, count the codes, compare the hash, and follow a note's link.
