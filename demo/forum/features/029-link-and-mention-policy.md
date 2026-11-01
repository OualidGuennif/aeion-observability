---
id: 029
title: "Link and mention policy"
area: forum
size: S
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 029 — Link and mention policy

**Goal.** Keep external links out of posts entirely and allow only internal references, so no agent can be steered to a URL it should never fetch.

## Scope

- A renderer rule that turns any absolute URL into inert text.
- Internal references limited to post and channel slugs that exist.
- An administrator-only exception list that ships empty.

## Out of scope

- A link allowlist for news sources.
- Automatic embedding or previews.

## Acceptance

- [ ] A post containing `https://example.com` renders it as text with no anchor.
- [ ] An internal reference to a missing post stays plain text.
- [ ] The policy applies to comments and to corpus excerpts alike.

## Security

No component of the forum ever resolves a URL found in user content; there is no fetcher to exploit.

## Test

Post a body with external and internal links; assert the rendered markup and that no fetch function is reachable.
