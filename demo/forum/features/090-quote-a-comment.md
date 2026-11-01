---
id: 090
title: "Quote a comment"
area: forum
size: S
parallel: false
depends_on: [022]
owner: builder
status: proposed
---

# 090 — Quote a comment

**Goal.** Quote a short excerpt of another comment with a reference by id, so a reply keeps its context without copying a whole body.

## Scope

- A quote record with source comment id, capped excerpt and the quoting comment.
- The excerpt rendered through the sanitizer and marked as a quote.
- A refusal to quote hidden content or more than the cap.

## Out of scope

- Nested quote chains.
- Quoting across channels.

## Acceptance

- [ ] A quote over the cap is truncated at a word boundary and says so.
- [ ] Quoting a held comment is refused.
- [ ] Deleting the source leaves the quote readable with the source marked unavailable.

## Security

The source must be visible to the quoter at the time of quoting; the check is server-side.

## Test

Quote a visible, a held and a deleted comment; assert acceptance, refusal and fallback.
