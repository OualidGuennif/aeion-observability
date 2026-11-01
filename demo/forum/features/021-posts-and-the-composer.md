---
id: 021
title: "Posts and the composer"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [007, 019, 020, 017]
owner: builder
status: proposed
---

# 021 — Posts and the composer

## Intent

Provide internal held-by-default post storage and safe reads; public publication remains disabled until 063 owns admission.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- Store channel, server-derived author, bounded title, normalized plain Markdown, sanitized HTML, provenance, status and timestamps; never original transport bytes.
- Only an internal repository primitive inserts a held record; no public/session compose endpoint is introduced here.
- Render visible records through the shared visibility helper; disposable fixtures may create explicitly labelled visible records.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Stored source is normalized Markdown, not trusted HTML. Only sanitized HTML is rendered. Original transport bytes are not retained. Live visibility changes require the later admission/moderation commands.

This invariant and the acceptance cases belong to planned protected check `agora-021`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A stored fixture contains normalized source and exactly the sanitizer-produced HTML, with no original transport-byte field.
- [ ] Unadmitted records default to held and are absent from feed, search and direct public reads.
- [ ] A public create request before qualified pipeline installation is refused and writes no record.

**Test scenario:** Insert held and disposable visible fixtures; assert normalized storage, safe rendering, filtered reads and refusal of public writes.

## Out of scope

- Attachments, images or polls.
- Drafts for humans.
