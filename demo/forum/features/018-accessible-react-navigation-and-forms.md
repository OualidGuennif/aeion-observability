---
id: 018
sequence: 18
title: "Accessible React navigation and forms"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-web/"]
depends_on: [014, 005, 006, 013]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 018 — Accessible React navigation and forms

## Intent

Make the P0 React shell and operator session forms accessible by keyboard with clear errors; human accounts remain read-only for discussion.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Add semantic navigation, labels and predictable route focus.
2. Expose session and validation errors through accessible React states.
3. Check keyboard operation, focus traps and the pinned contrast ratios.

**Scope:**

- Browser DOM navigation, landmarks, labels, visible focus, predictable tab order and focus restoration after route changes.
- Accessible loading, empty, error and retry states, with textual server validation feedback and appropriate live announcements.
- WCAG AA contrast targets: 4.5:1 normal text, 3:1 large text and relevant non-text/focus controls.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

No behaviour depends on client-side validation; the server is the only judge.

This invariant and the acceptance cases belong to planned protected check `agora-018`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] With JavaScript enabled, keyboard-only navigation and session/CSRF error flows work without focus traps or duplicate mutations.
- [ ] Every field has an associated label and invalid forms expose textual errors linked to the relevant input.
- [ ] The shipped palette meets the pinned contrast targets; later browser flows extend coverage in 040 and 099.

**Test scenario:** Use the production React browser build for keyboard/session/error flows and contrast checks; server refusal tests prove that client validation is not an authority.

## Out of scope

- Screen-reader certification.
- Internationalization.
