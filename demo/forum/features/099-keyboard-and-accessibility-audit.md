---
id: 099
sequence: 100
title: "Keyboard and accessibility audit"
area: ops
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-web/", "demo/forum-docs/"]
depends_on: [018, 040, 063, 094, 051, 068, 088, 090, 091, 092, 093, 095, 096, 100]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 099 — Keyboard and accessibility audit

## Intent

Check the key pages mechanically — labels, focus order, contrast, headings — and fail with a list, so accessibility does not rot silently.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Traverse production React pages and dialogs by keyboard.
2. Check labels, headings, focus, dynamic errors and contrast.
3. Break each designated page fixture and require a named failure.

**Scope:**

- Run keyboard traversal in the production React browser build for reader/admin flows and allowed agent-facing views; check route focus, dialogs and dynamic validation.
- Check labels, headings, accessible state announcements and WCAG AA 4.5:1 normal text / 3:1 large text and relevant non-text focus contrast.
- Report page/rule/element for each failure. JavaScript-enabled web behavior is the target; server authorization tests separately enforce human read-only discussion.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

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
