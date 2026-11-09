---
id: 000
sequence: <1..N topological sequence>
title: "<Short imperative feature title>"
area: <foundation | forum | moderation | agents | corpus | ops>
size: <S | M | L>
parallel: false
phase: <P0 | P1 | P2 | P3 | P4 | P5>
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [<prerequisite feature IDs, e.g. 001, 002>]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 000 — <Short imperative feature title>

## Intent

<State in 1..2 sentences the user, operator, or platform capability this feature delivers and why it is needed now.>

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_<a..f>.py`.

## Inputs

**Delivery steps:**

1. <Implement the focused backend resource, migration, or React view inside the declared write scopes.>
2. <Wire request validation, deterministic error codes, and persistence or UI state transitions.>
3. <Add JUnit/Quarkus or React production build tests covering positive and refusal paths, and update the product docs.>

**Scope:**

- <Primary deliverable inside `demo/forum-app/`, `demo/forum-web/`, or `demo/forum-docs/`.>
- <Data contract, schema migration, or UI component boundary with explicit field and status rules.>
- <Telemetry, audit, or operational health surface required to observe the feature safely.>

**Authoring checklist (canonical source: `demo/forum/tools/specs_a.py`..`specs_f.py`):**
- Define `id`, `title`, `area`, `size`, `phase`, `tier: 3`, `parallel: False`, `deps`, and `write_paths`.
- Include `knowledge/components/agora-product.md` and `knowledge/components/factory-architecture.md` in `write_paths`.
- Keep `delivery` to 2..4 concrete steps (<= 220 chars each) and run `python3 demo/forum/tools/generate_features.py`.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

<State the fail-closed security, privacy, and authority invariant (unauthenticated/unauthorized refusal, untrusted input handling, and absence of raw secrets or prompts in logs/telemetry).>

This invariant and the acceptance cases belong to planned protected check `agora-000`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] <Positive check: valid input produces the expected HTTP status, persisted row, or rendered UI state.>
- [ ] <Refusal check: missing auth, invalid payload, or unavailable dependency fails closed with an explicit code.>
- [ ] <Regression check: protected unit/integration suite and product knowledge docs stay in sync.>

**Test scenario:** <Describe the reproducible end-to-end JUnit/Quarkus or browser verification scenario, including setup, action, expected response, and refusal assertion.>

## Out of scope

- <Adjacent capability deferred to a later feature ID so this slice remains bounded.>
- <Forbidden shortcut (e.g. bypassing migrations, weakening checks, or touching undeclared paths).>
