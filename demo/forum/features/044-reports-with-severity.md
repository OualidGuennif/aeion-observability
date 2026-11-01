---
id: 044
title: "Reports with severity"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [021, 022, 020, 041, 043]
owner: builder
status: proposed
---

# 044 — Reports with severity

## Intent

Let an identity report a post or comment with one rule code and an optional note, deduplicated per reporter, so the queue reflects distinct complaints rather than clicks.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- `reports` table with target, reporter, rule code, note, state.
- One open report per reporter and target.
- A refusal to report content the reporter cannot see.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The reporter's identity is server-derived and never shown to the reported author.

This invariant and the acceptance cases belong to planned protected check `agora-044`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The same reporter filing twice keeps one open report.
- [ ] A report with an unknown rule code answers 422.
- [ ] Reporting hidden content answers 404.

**Test scenario:** File duplicate reports, an invalid code and a hidden target; assert one row and the two refusals.

## Out of scope

- Anonymous reporting.
- Reports against identities rather than content.
