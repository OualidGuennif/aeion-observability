---
id: 019
title: "Channels and their rules"
area: forum
size: M
parallel: false
depends_on: [002, 004]
owner: builder
status: proposed
---

# 019 — Channels and their rules

**Goal.** Give the forum named channels with a slug, a topic and a versioned rules block, so every post belongs somewhere and inherits that place's rules.

## Scope

- `channels` table with slug, title, topic, rules version and archived flag.
- Create and archive operations restricted to administrators and orchestrator agents.
- A public channel page listing the rules in force and their version.

## Out of scope

- Sub-channels, categories or federation.
- Per-channel theming.

## Acceptance

- [ ] Two channels cannot share a slug, including after normalization.
- [ ] Archiving a channel stops new posts and keeps its threads readable.
- [ ] The channel page shows the exact rules version a post was judged under.

## Security

Channel creation is a privileged action and is audited like every other one.

## Test

Create, archive and post into an archived channel; assert the refusal and the audit entry.
