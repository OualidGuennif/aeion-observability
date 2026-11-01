---
type: Policy
title: "UI and UX"
description: "Sober interfaces: tokens in one file with light and dark sets, AA contrast, phone first, shared blocks, unknown never reads as fine, a visual yes before shipping."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: guide
    resource: ../../efficiency/1-quarks.md
    title: "Phase 1 of the guide"
---

# UI and UX

Sober and exact rather than decorative.

## Tokens

- Every colour, radius, font size and spacing value is a token in one file, with a light and a
  dark set (system preference and an explicit choice). A hard-coded colour is a dark-mode bug.
- Text meets WCAG AA (4.5:1). One primary colour and one accent; amber and red only for meaning.
- A spacing scale (for example 4, 8, 12, 16, 20, 28, 44 px) and a type scale; tabular figures for
  amounts and times.

## Layout and behaviour

- Phone first: every changed screen checked at 375 px and 1440 px, light and dark. Tables stack
  into cards on small screens; touch targets are at least 44 px; a bottom tab bar on phones when
  there are a few destinations.
- Shared building blocks before new components: page header, section, stat, meter, list, card.
- No inline styles (a strict content security policy will drop them).
- Motion only to show a change of state (140–220 ms), none under reduced motion.
- A plain wordmark; no ornament that carries no information; no caption that says nothing.

## Truthfulness

- An unknown or missing value reads "unknown", never "fine"; a blank is not zero.
- A visual change gets a human's visual yes before it ships.
