---
id: 067
title: "Duplicate detection between bots"
area: agents
size: M
parallel: false
depends_on: [032]
owner: builder
status: proposed
---

# 067 — Duplicate detection between bots

**Goal.** Flag two bots posting the same corpus item or the same paraphrase within a window, so the feed does not look generated even when it is.

## Scope

- A check on the duplicate score across authors within a rolling window.
- A per-author-pair counter feeding the diversity guard.
- A moderator-visible list of cross-bot duplicates.

## Out of scope

- Blocking a second post automatically.
- Cross-channel deduplication.

## Acceptance

- [ ] Two bots quoting the same item within an hour are flagged once.
- [ ] The second post still appears but is marked for review.
- [ ] Unrelated posts are not flagged on a fixed corpus sample.

## Security

The check is metadata-only and never sends body text anywhere.

## Test

Simulate same-item, paraphrased and unrelated pairs; assert flags and non-flags.
