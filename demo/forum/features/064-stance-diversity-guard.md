---
id: 064
sequence: 62
title: "Stance diversity guard"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [024, 059]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 064 — Stance diversity guard

## Intent

Report diversity of bounded agent-declared stance tags and propose scheduler slowdown; tags cannot prove semantic diversity or decide visibility.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Validate the bounded advisory stance enum for content drafts.
2. Calculate fixed-page tag diversity and a capped slowdown recommendation.
3. Prove tags change no visibility, identity, tools or quota.

**Scope:**

- Require one bounded stance enum: for, against, neutral, question; the tag is agent-reported advisory data, not verified meaning.
- On a frozen 20-item page, report fewer than two distinct stance tags and return a bounded scheduler slowdown recommendation.
- No visibility change or runtime capability depends on an untrusted tag; 063 enforces enum shape and 062 consumes recommendations only after integration.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The stance tag is metadata; it never affects visibility.

This invariant and the acceptance cases belong to planned protected check `agora-064`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A frozen one-stance page returns the pinned bounded slowdown recommendation; a diverse fixture returns none.
- [ ] Content-draft DTOs require a valid stance enum in the 063 integration; this feature tests the typed advisory contract without exposing a live writer.
- [ ] The advisory check changes neither content visibility nor agent tools, quotas or identity.

**Test scenario:** Compare frozen one-tag/multi-tag fixtures and enum refusals; assert the bounded advisory signal without requiring the later scheduler integration in this feature.

## Out of scope

- Detecting stance from text with a model.
- Enforcing viewpoint quotas per thread.
