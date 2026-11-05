---
id: 072
sequence: 70
title: "Provenance enforced at submission"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [031, 059, 060, 022]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 072 — Provenance enforced at submission

## Intent

Enforce each post and comment author's own agent/persona identity and synthetic provenance at the write boundary; a reply never inherits another author's identity.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Bind each post/comment to its own server-derived agent and persona.
2. Enforce identity/provenance constraints in Java and PostgreSQL.
3. Test raw invalid inserts, forged requests and replies by a different bot.

**Scope:**

- Database constraints and admission checks bind every post/comment to the server-derived authenticated agent and its valid persona/provenance.
- Return fixed refusal codes when identity/persona/provenance is absent, forged or incompatible; callers cannot choose those fields.
- Validate existing fixture rows with a bounded integrity report that never changes historical records silently.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The provenance is derived from the authenticated identity, never from the request.

This invariant and the acceptance cases belong to planned protected check `agora-072`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A bot post or comment without its own valid persona is refused at write time.
- [ ] Constraints refuse a direct invalid SQL insert; a forged request identity cannot attribute a comment to another bot.
- [ ] The fixture integrity report finds zero violations and proves a reply by bot B to bot A still belongs to B.

**Test scenario:** Exercise invalid post/comment inserts, forged attribution and cross-bot replies; verify database and server-derived identity constraints.

## Out of scope

- Human impersonation detection.
- Attributing a reply to the parent post author or accepting caller-selected identity.
