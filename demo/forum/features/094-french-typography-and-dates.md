---
id: 094
sequence: 96
title: "French typography and dates"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-web/"]
depends_on: [014]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 094 — French typography and dates

## Intent

Apply French conventions — non-breaking spaces before punctuation, guillemets, and readable dates — without a localization framework.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Add French plain-text formatting and explicit date/time helpers.
2. Apply them only to appropriate React text nodes, never stored or HTML data.
3. Pin punctuation, seven-day switching and Europe/Paris DST fixtures.

**Scope:**

- Use shared React plain-text formatting helpers for French punctuation/quotes, never modify serialized HTML, code blocks, URLs or attributes.
- Use Intl.DateTimeFormat with French locale and Europe/Paris; freeze the reference instant for relative times and switch to an absolute date after seven days.
- Pin twenty Unicode/date fixtures including DST boundaries and preserve the original normalized storage representation.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Typography transforms plain text nodes before final escaping, never serialized HTML or attributes; it cannot introduce markup or change an authorization decision.

This invariant and the acceptance cases belong to planned protected check `agora-094`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A colon, semicolon, question or exclamation mark renders after a non-breaking space.
- [ ] Guillemets close correctly around a quoted phrase.
- [ ] Relative times switch to absolute dates after a week.

**Test scenario:** A table of twenty strings, asserted character by character.

## Out of scope

- Other languages.
- A translation workflow.
