---
id: 044
title: "Reports with severity"
area: moderation
size: M
parallel: false
depends_on: [021]
owner: builder
status: proposed
---

# 044 — Reports with severity

**Goal.** Let an identity report a post or comment with one rule code and an optional note, deduplicated per reporter, so the queue reflects distinct complaints rather than clicks.

## Scope

- `reports` table with target, reporter, rule code, note, state.
- One open report per reporter and target.
- A refusal to report content the reporter cannot see.

## Out of scope

- Anonymous reporting.
- Reports against identities rather than content.

## Acceptance

- [ ] The same reporter filing twice keeps one open report.
- [ ] A report with an unknown rule code answers 422.
- [ ] Reporting hidden content answers 404.

## Security

The reporter's identity is server-derived and never shown to the reported author.

## Test

File duplicate reports, an invalid code and a hidden target; assert one row and the two refusals.
