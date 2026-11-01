---
id: 032
title: "Content hashing and near-duplicates"
area: forum
size: M
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 032 — Content hashing and near-duplicates

**Goal.** Hash every normalized body and detect near-duplicates with a shingle comparison, so spam and copy-paste floods are visible before they rank.

## Scope

- A sha256 of the normalized body stored with each post.
- A five-shingle fingerprint and a similarity query over recent posts.
- A duplicate score attached to the post for the moderation queue.

## Out of scope

- Blocking on similarity, which is a moderation decision, not a storage one.
- Cross-language detection.

## Acceptance

- [ ] The same body with different whitespace yields the same hash.
- [ ] Two paraphrased bodies above the threshold are flagged with a score.
- [ ] The duplicate query stays under the recorded budget on ten thousand posts.

## Security

Hashes never leave the database; neither the hash nor the score appears in telemetry.

## Test

Insert whitespace variants, a paraphrase and an unrelated body; assert the hash equality and the flagging.
