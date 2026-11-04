---
id: 100
sequence: 99
title: "Community guidelines page"
area: ops
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [041, 014, 082]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 100 — Community guidelines page

## Intent

Publish the rules as a human-readable guide with one example per rule code, generated from the same file the engine uses, so readers and moderators read the same text.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Render public rule prose/examples from retained versioned data.
2. Add the React guidelines/about views and synthetic corpus note.
3. Check exact rule coverage/hash and authorized historical-rule links.

**Scope:**

- Render each rule code with prose and one allowed/refused example, with the exact version stamp.
- Expose an about page integrating docs/corpus-license.md and the synthetic source statement.
- Link moderation notes to the cited retained rules version; private channel rules require membership.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The guide is generated from the reviewed rules file; it has no write path.

This invariant and the acceptance cases belong to planned protected check `agora-100`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every rule code appears exactly once.
- [ ] The version stamp equals the rules hash in force.
- [ ] A moderation note's link opens the cited rule.

**Test scenario:** Render, count the codes, compare the hash, and follow a note's link.

## Out of scope

- A commentable policy or a legal notice.
- Per-language versions.
