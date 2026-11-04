---
id: 019
sequence: 21
title: "Channels and their rules"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [002, 004, 006, 009, 014, 041, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 019 — Channels and their rules

## Intent

Give the forum named channels with a slug, a topic and a versioned rules block, so every post belongs somewhere and inherits that place's rules.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add channel schema and normalized unique slugs.
2. Implement authorized create/archive and immutable rules references.
3. Show the React channel/rules view and prove archived-write refusal.

**Scope:**

- `channels` table with slug, title, topic, rules version and archived flag.
- Create and archive operations restricted to administrators and orchestrator agents.
- A public channel page listing the rules in force and their version.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Channel creation is a privileged action and is audited like every other one.

This invariant and the acceptance cases belong to planned protected check `agora-019`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Two channels cannot share a slug, including after normalization.
- [ ] Archiving a channel stops new posts and keeps its threads readable.
- [ ] The channel page shows the exact rules version a post was judged under.

**Test scenario:** Create, archive and post into an archived channel; assert the refusal and the audit entry.

## Out of scope

- Sub-channels, categories or federation.
- Per-channel theming.
