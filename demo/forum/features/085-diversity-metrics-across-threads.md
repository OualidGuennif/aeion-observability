---
id: 085
title: "Diversity metrics across threads"
area: corpus
size: S
parallel: false
depends_on: [084]
owner: builder
status: proposed
---

# 085 — Diversity metrics across threads

**Goal.** Report per day how many distinct items, categories and authors appear in the first page of each channel, so 'looks alive' is measured.

## Scope

- A daily computation written to a small table and shown in the cockpit.
- Three metrics with documented targets.
- A failure line when a target is missed for two consecutive days.

## Out of scope

- Per-reader ranking metrics.
- Model-based quality judgment.

## Acceptance

- [ ] The metrics reproduce from the raw tables in a test.
- [ ] A day with one author everywhere reports the miss.
- [ ] The report names the channel and the metric, not a person.

## Security

Metrics aggregate identifiers into counts; no body text is read.

## Test

Pin a day of data, compute, and compare with a hand-written expectation.
