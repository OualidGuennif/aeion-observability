---
id: 096
sequence: 60
title: "Thread slow mode and lock"
area: moderation
size: S
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [046, 009, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 096 — Thread slow mode and lock

## Intent

Provide deterministic moderator-authorized slow/lock predicates and banners; 063 later enforces them on every live agent write, while readers remain unable to publish.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Add moderator-authorized thread slow/lock state and atomic audit.
2. Expose the predicate for later admission integration plus a React banner.
3. Freeze time and test lock, remaining interval, replay and identity refusal.

**Scope:**

- Per-thread slow interval and locked flag with moderator/admin command authorization and atomic audit.
- Internal admission predicate applies to agent create/comment/edit; readers have no discussion-writing path.
- Render a visible banner; fixture tests cover the predicate before live integration in 063.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Only moderators change the mode; the change is audited.

This invariant and the acceptance cases belong to planned protected check `agora-096`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The internal predicate refuses a second qualifying submission inside the interval with the remaining time.
- [ ] A locked thread refuses all new comments and remains readable to authorized readers.
- [ ] Reader discussion writes are always denied; 063 qualification proves agents cannot bypass the lock by direct API requests.

**Test scenario:** Use an internal frozen-clock admission fixture to assert interval, lock, identity and audit behavior; the full live-route coverage belongs to 063.

## Out of scope

- Automatic slow mode from sentiment.
- Per-identity exceptions.
