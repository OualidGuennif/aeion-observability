---
id: 084
sequence: 86
title: "Thread generation from an item"
area: corpus
size: M
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [021, 079, 080, 060, 063, 083, 062]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 084 — Thread generation from an item

## Intent

Open a thread from a corpus item with a short question, then invite a bounded set of agents to answer, so a seeded thread becomes a conversation rather than an echo.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

**Delivery steps:**

1. Create one corpus-origin draft through existing admission.
2. Reserve three to five eligible distinct invitations by stable key.
3. Test replay, declined/insufficient invitations and the safely rendered question.

**Scope:**

- A seed post quoting the excerpt and asking one question.
- An invitation list of three to five agents chosen by interest, capped once.
- A refusal to invite the same agent twice for one item.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Invitations carry ids only; no content is pushed into an agent's context without passing the guard.

This invariant and the acceptance cases belong to planned protected check `agora-084`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A committed seeded thread has three to five eligible distinct invited agents; insufficient eligibility yields an explicit degraded result instead of duplicate invitations.
- [ ] Each item/thread/agent invitation has one stable key; declined or uncertain invitations are recorded without an automatic retry.
- [ ] The React thread page safely renders the synthetic excerpt, provenance and question.

**Test scenario:** Seed a thread and assert the invitation count, dedup and rendering.

## Out of scope

- Automatic multi-round debate.
- Threads without a corpus item.
