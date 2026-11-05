---
id: 017
sequence: 17
title: "Strict request validation"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [001]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 017 — Strict request validation

## Intent

Reject unknown fields, wrong types and oversized bodies at the edge, so no handler ever receives a shape it did not declare.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Declare strict Jackson DTOs and bounded Jakarta validation.
2. Enforce the early byte cap without consuming the handler input stream.
3. Test unknown fields, malformed types, missing fields and oversize bodies.

**Scope:**

- Use Jackson DTOs with strict unknown-property and primitive/type handling plus Jakarta validation for required fields and bounded strings; do not introduce Python request models.
- Enforce the 16384-byte body cap before JSON parsing and restore the bounded input stream for the Quarkus handler.
- Return 422 with field paths and fixed codes only; malformed JSON and unsupported shapes never expose supplied values.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The limit applies to every route, including the agent API, before authentication work.

This invariant and the acceptance cases belong to planned protected check `agora-017`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An extra field returns 422 before the handler runs.
- [ ] A body exceeding 16384 bytes returns 413 after reading at most the cap plus one byte; parsing/allocation remain bounded.
- [ ] A missing required field names only its path, without its value.

**Test scenario:** Send an extra field, an oversized body and a missing field to a sample route and assert each answer.

## Out of scope

- Content negotiation or versioned request formats.
- Custom coercion rules.
