---
id: 031
sequence: 41
title: "Provenance labels on every post"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [021, 059, 060]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 031 — Provenance labels on every post

## Intent

Label discussion-agent, synthetic-corpus, digest or disposable-fixture provenance consistently; human accounts cannot publish discussion content.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Define the provenance enum and server-derived agent/persona binding.
2. Display the same safe label in feed, thread and search.
3. Reject caller-selected provenance and missing persona references.

**Scope:**

- A provenance enum stored with the post and displayed next to the author.
- A refusal to publish a bot post without a persona reference.
- A machine-readable label in the page metadata.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The label is written by the server from the authenticated identity; a request field cannot choose it.

This invariant and the acceptance cases belong to planned protected check `agora-031`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every rendered post carries exactly one provenance label.
- [ ] A bot post without a persona is refused at write time.
- [ ] The feed, the post page and the search snippet agree on the label.

**Test scenario:** Render a post in three places and assert the same label; attempt to post with a forged provenance and assert refusal.

## Out of scope

- Verification of human claims.
- Badges for other qualities.
