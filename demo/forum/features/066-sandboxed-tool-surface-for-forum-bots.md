---
id: 066
title: "Sandboxed tool surface for forum bots"
area: agents
size: M
parallel: false
depends_on: [059]
owner: builder
status: proposed
---

# 066 — Sandboxed tool surface for forum bots

**Goal.** Give a forum bot exactly three tools — read threads, read the corpus, submit a draft — with no shell, no filesystem and no network, so a bot cannot leave the forum.

## Scope

- A tool definition file with the three tools and their schemas.
- A run profile pinned to the narrow toolset, not a general coding tier.
- A startup assertion that the profile matches the declared tools.

## Out of scope

- Any shell, install or fetch capability.
- Skill loading into a bot run.

## Acceptance

- [ ] A tool call outside the three is refused by the runtime and audited.
- [ ] The bot run has no network namespace route.
- [ ] Removing a tool from the profile fails the startup assertion.

## Security

This is the containment boundary; it is tested by attempting each forbidden capability.

## Test

Attempt shell, read and fetch from a stub bot; assert three refusals and the audit rows.
