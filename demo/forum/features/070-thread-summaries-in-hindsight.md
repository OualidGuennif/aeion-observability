---
id: 070
title: "Thread summaries in Hindsight"
area: agents
size: M
parallel: false
depends_on: [069]
owner: builder
status: proposed
---

# 070 — Thread summaries in Hindsight

**Goal.** Retain one short analysis per finished thread in Hindsight with the policy tags, so an agent can recall themes without re-reading every body.

## Scope

- A summarizer that runs offline on a closed thread and writes one record.
- Tags for category, tone and outcome, never handles.
- A retention window and a delete operation.

## Out of scope

- Semantic search in the product UI.
- Summarizing held content.

## Acceptance

- [ ] A closed thread yields exactly one retained record.
- [ ] The record carries no handle and no verbatim sentence over forty characters.
- [ ] Deleting a thread deletes its record within one run.

## Security

Summaries are generated from public text only and stored in the demo's synthetic namespace.

## Test

Close, summarize, delete; assert counts, the absence of handles and the deletion.
