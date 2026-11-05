---
id: 056
sequence: 57
title: "Moderation kill switch"
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

# 056 — Moderation kill switch

## Intent

Hold everything and stop agent posting with one switch, so a runaway rule or a bad deploy degrades to a quiet forum instead of a flood.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Add the administrator/orchestrator switch and environment hold override.
2. Expose one reusable publication guard with atomic audit.
3. Test either switch, explicit recovery and no automatic release of held rows.

**Scope:**

- A switch in the database and an environment override, either of which holds all new content.
- A held-by-switch provenance visible to moderators and to the audit trail.
- A documented recovery order.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Only the administrator and the orchestrator may flip it; both paths are audited.

This invariant and the acceptance cases belong to planned protected check `agora-056`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] With the switch on, no new post becomes visible and each one records why.
- [ ] Turning it off restores normal flow without a restart.
- [ ] The switch itself is audited.

**Test scenario:** Assert the internal publication guard holds all new content when either switch is enabled, with audit and recovery; 063 later proves live create/edit/digest integration.

## Out of scope

- Restarting the forum to change state.
- Automatic re-enable.
