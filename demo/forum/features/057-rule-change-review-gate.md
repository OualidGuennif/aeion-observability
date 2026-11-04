---
id: 057
sequence: 58
title: "Rule change review gate"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [041, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 057 — Rule change review gate

## Intent

Make a rule change a reviewed commit with a fixture diff, so a rule cannot be loosened to let a specific post through.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Compare rule/version changes with retained citations and fixture changes.
2. Produce the bounded human-readable rule diff for review.
3. Refuse missing coverage or cited-code removal; tests cannot grant approval.

**Scope:**

- A check that the rules file changed together with a test or a fixture diff.
- A rendered diff of the public rules page in the pull request body.
- A refusal to ship a code removal that old posts cite.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

A fixture diff is necessary but not approval. Rules changes always require owner review and protected checks; candidate-controlled tests cannot certify their own change.

This invariant and the acceptance cases belong to planned protected check `agora-057`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A rules change without a fixture or test change fails the check.
- [ ] The pull request body shows the rendered diff.
- [ ] Removing a cited code is refused.

**Test scenario:** Change the rules alone and assert failure; change with a fixture and assert pass.

## Out of scope

- Approval workflows inside the app.
- Versioned rule branches.
