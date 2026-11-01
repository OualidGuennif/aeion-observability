---
id: 077
title: "Two hundred synthetic French items"
area: corpus
size: M
parallel: false
depends_on: [075]
owner: builder
status: proposed
---

# 077 — Two hundred synthetic French items

**Goal.** Write two hundred plausible French news items across tech, state and government, clearly synthetic, so the forum has material without touching a real outlet.

## Scope

- Two hundred items with varied length, all labelled synthetic and attributed to invented sources.
- At least forty per category, spread over six months.
- A short style note so the corpus reads consistently.

## Out of scope

- Any quotation of a real publication.
- Political advocacy or personally identifying content.

## Acceptance

- [ ] Every item validates against the schema and carries the label.
- [ ] No item names a real outlet as its source.
- [ ] Category counts meet the minimum.

## Security

The corpus is data, never instructions; it is scanned by the injection guard like any body.

## Test

Validate all items, then grep for a list of real outlet names to assert none appears as a source.
