---
id: 099
title: "Keyboard and accessibility audit"
area: ops
size: S
parallel: false
depends_on: [018]
owner: builder
status: proposed
---

# 099 — Keyboard and accessibility audit

**Goal.** Check the key pages mechanically — labels, focus order, contrast, headings — and fail with a list, so accessibility does not rot silently.

## Scope

- A script parsing the rendered HTML for missing labels, broken heading order and focus traps.
- A contrast computation over the shipped palette.
- A report by page and by rule.

## Out of scope

- Screen-reader testing.
- Certification.

## Acceptance

- [ ] Each check fails on a deliberately broken page.
- [ ] The report names the page, the rule and the element.
- [ ] The script runs on the seeded instance in CI.

## Security

The audit is read-only against a disposable instance.

## Test

Run on the seed and on a broken fixture; assert the pass and the named failures.
