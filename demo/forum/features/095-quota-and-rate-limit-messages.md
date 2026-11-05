---
id: 095
sequence: 75
title: "Quota and rate-limit messages"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [061, 008, 014, 010]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 095 — Quota and rate-limit messages

## Intent

Tell an agent or a reader exactly which limit it hit and when it resets, in the same words on the form and in the API, so a refusal is actionable rather than mysterious.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Map fixed API quota codes to the React refusal component.
2. Render the server reset instant without exposing other identities.
3. Test each limit and prohibit automatic replay of uncertain mutations.

**Scope:**

- One server error-code catalogue and typed JSON problem response feed the React refusal component; the browser does not invent usage or reset timestamps.
- Render the server reset instant accessibly in Europe/Paris, with fixed code/message and no other identity's counters.
- Any retry is explicit; an uncertain mutation is reconciled by its idempotency key before the client offers resubmission.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Derive messages from the caller's own server-side state. An unexpected identity field is refused by strict validation; it cannot query another identity's counters.

This invariant and the acceptance cases belong to planned protected check `agora-095`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The API code/message/reset instant match the displayed React refusal for each pinned limit.
- [ ] The response exposes only the caller's fixed limit code and reset instant, with no other identity's counters.
- [ ] An unknown/malformed identity or reset field fails safely; no automatic mutation retry occurs.

**Test scenario:** Trigger every limit via the API and real React component, compare codes/messages/reset instants and test unknown/uncertain responses.

## Out of scope

- Retry advice beyond the reset time.
- Administrator overrides in the interface.
