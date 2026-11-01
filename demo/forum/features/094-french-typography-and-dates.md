---
id: 094
title: "French typography and dates"
area: forum
size: S
parallel: false
depends_on: [014]
owner: builder
status: proposed
---

# 094 — French typography and dates

**Goal.** Apply French conventions — non-breaking spaces before punctuation, guillemets, and readable dates — without a localization framework.

## Scope

- A text filter used by every template for punctuation spacing and quotes.
- Date rendering in French, with relative times for recent posts.
- A test table of typographic cases.

## Out of scope

- Other languages.
- A translation workflow.

## Acceptance

- [ ] A colon, semicolon, question or exclamation mark renders after a non-breaking space.
- [ ] Guillemets close correctly around a quoted phrase.
- [ ] Relative times switch to absolute dates after a week.

## Security

The filter runs after sanitization and never reintroduces markup.

## Test

A table of twenty strings, asserted character by character.
