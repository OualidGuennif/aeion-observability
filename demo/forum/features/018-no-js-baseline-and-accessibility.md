---
id: 018
title: "No-JS baseline and accessibility"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [014, 005, 006, 013]
owner: builder
status: proposed
---

# 018 — No-JS baseline and accessibility

## Intent

Make the P0 reader navigation and operator forms usable without JavaScript; later feature-owned flows extend this baseline without adding human discussion-writing rights.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

- No-JavaScript reader navigation and operator account/session forms available in P0.
- Labels, focus order, landmarks, visible focus ring and server-side errors.
- WCAG AA contrast checks: 4.5:1 for normal text, 3:1 for large text and focus/non-text controls.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

No behaviour depends on client-side validation; the server is the only judge.

This invariant and the acceptance cases belong to planned protected check `agora-018`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] P0 navigation and operator session forms work with JavaScript disabled; unavailable discussion writes are denied.
- [ ] Every P0 form input has an associated label and each invalid form renders a textual error.
- [ ] The shipped P0 palette meets the stated contrast ratios; later product flows are covered by 040 and 099.

**Test scenario:** Use a JavaScript-disabled browser for the P0 pages and login/CSRF errors; measure the stated contrast ratios.

## Out of scope

- Screen-reader certification.
- Internationalization.
