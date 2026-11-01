---
id: 027
title: "Tags and topics"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 027 — Tags and topics

**Goal.** Attach a small set of controlled tags to posts, so threads can be grouped by topic without free-form taxonomy drift.

## Scope

- A `tags` table seeded from a fixed list and a join table to posts.
- At most three tags per post, chosen from the list only.
- Tag pages listing posts with the tag.

## Out of scope

- User-created tags.
- Tag hierarchies.

## Acceptance

- [ ] An unknown tag is refused, not created.
- [ ] A fourth tag answers 422.
- [ ] A tag page lists only posts the reader may see.

## Security

Tag names are rendered escaped and never used as raw CSS classes.

## Test

Create posts with zero, three and four tags; assert acceptance, the cap and the visibility filter.
