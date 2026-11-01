---
id: 080
title: "Corpus citation in posts"
area: corpus
size: S
parallel: false
depends_on: [021, 075]
owner: builder
status: proposed
---

# 080 — Corpus citation in posts

**Goal.** Attach the source item id to a thread and show a short, sanitized excerpt on the post page, so the discussion is traceable to the synthetic item it started from.

## Scope

- A nullable corpus reference on the post and a rendered excerpt block.
- The excerpt rendered through the sanitizer, labelled synthetic.
- A refusal to attach an item from another channel's category policy.

## Out of scope

- Full article rendering.
- External links to the item.

## Acceptance

- [ ] A post with a corpus reference shows the excerpt and the synthetic label.
- [ ] Deleting the corpus item leaves the post readable with the reference marked unavailable.
- [ ] No link is generated.

## Security

The excerpt is sanitized text; the reference is an internal id, never a URL.

## Test

Attach, delete and render; assert the label, the fallback and the absence of anchors.
