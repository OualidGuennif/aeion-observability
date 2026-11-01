---
id: 080
title: "Corpus citation in posts"
area: corpus
size: S
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 075, 029, 020, 007]
owner: builder
status: proposed
---

# 080 — Corpus citation in posts

## Intent

Attach the source item id to a thread and show a short, sanitized excerpt on the post page, so the discussion is traceable to the synthetic item it started from.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- A nullable corpus reference on the post and a rendered excerpt block.
- The excerpt rendered through the sanitizer, labelled synthetic.
- A refusal to attach an item from another channel's category policy.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The excerpt is sanitized text; the reference is an internal id, never a URL.

This invariant and the acceptance cases belong to planned protected check `agora-080`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A post with a corpus reference shows the excerpt and the synthetic label.
- [ ] Deleting the corpus item leaves the post readable with the reference marked unavailable.
- [ ] No link is generated.

**Test scenario:** Attach, delete and render; assert the label, the fallback and the absence of anchors.

## Out of scope

- Full article rendering.
- External links to the item.
