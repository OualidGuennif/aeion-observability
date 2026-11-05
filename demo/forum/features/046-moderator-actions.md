---
id: 046
sequence: 48
title: "Moderator actions"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [042, 045, 009, 043, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 046 — Moderator actions

## Intent

Offer a small, audited action set — hold, approve, reject, lock, escalate — with a mandatory reason code, so every change of visibility is explainable.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Define the small moderation command set and idempotent action identity.
2. Commit state and audit together after current deterministic recomputation.
3. Test every action, replay, missing code and visibility atomicity.

**Scope:**

- Actions applied through one command that writes the state and the audit entry together.
- A mandatory rule code and an optional note per action.
- Idempotency: applying the same action twice is a no-op with a 200.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Commit visibility and audit atomically. Approval recomputes the deterministic verdict on current content/rules; only the separately authorized owner override can overrule it.

This invariant and the acceptance cases belong to planned protected check `agora-046`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A hold removes the post from public reads within the same transaction.
- [ ] An action without a rule code is refused.
- [ ] A repeated action leaves one audit entry.

**Test scenario:** Apply each action, repeat one, omit the code; assert state, visibility and audit rows.

## Out of scope

- Bulk actions over a filter.
- Undo beyond an explicit restore action.
