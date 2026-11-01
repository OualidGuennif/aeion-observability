---
id: 082
title: "Licensing and provenance note"
area: corpus
size: S
parallel: false
depends_on: [075]
owner: builder
status: proposed
---

# 082 — Licensing and provenance note

**Goal.** Document that the corpus is synthetic, how to replace it with licensed material, and what must change — so nobody ships real news through this path by accident.

## Scope

- A note in the corpus directory and on the forum's about page.
- The list of changes a real source requires: attribution fields, retention, and review.
- A startup check that refuses `synthetic: false` while the deployment flag is demo.

## Out of scope

- A licensed feed integration.
- Legal advice.

## Acceptance

- [ ] The about page states the corpus is synthetic.
- [ ] A non-synthetic item is refused while the flag is demo.
- [ ] The note names the fields a real source would need.

## Security

The flag is server-side configuration, not a request parameter.

## Test

Flip the flag and assert the refusal; render the about page and assert the statement.
