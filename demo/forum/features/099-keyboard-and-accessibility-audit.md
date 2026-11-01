---
id: 099
title: "Keyboard and accessibility audit"
area: ops
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [018, 040, 063, 094]
owner: builder
status: proposed
---

# 099 — Keyboard and accessibility audit

## Intent

Check the key pages mechanically — labels, focus order, contrast, headings — and fail with a list, so accessibility does not rot silently.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- Run browser-based keyboard traversal for reader, administrator and allowed agent-facing views; static HTML checks alone cannot detect focus traps.
- Check labels/headings plus WCAG AA 4.5:1 normal text and 3:1 large text/non-text focus contrast.
- Report by page/rule/element; JavaScript-disabled flows respect the human read-only discussion policy.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

The audit is read-only against a disposable instance.

This invariant and the acceptance cases belong to planned protected check `agora-099`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Each check fails on a deliberately broken page.
- [ ] The report names the page, the rule and the element.
- [ ] The script runs on the seeded instance in CI.

**Test scenario:** Run on the seed and on a broken fixture; assert the pass and the named failures.

## Out of scope

- Screen-reader testing.
- Certification.
