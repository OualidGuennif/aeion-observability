---
id: 048
sequence: 50
title: "Bans, mutes and cooldowns"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [043, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 048 — Bans, mutes and cooldowns

## Intent

Apply reasoned sanctions with explicit expiry and server-side write enforcement; permanent sanctions require the separately authorized administrator path.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Add explicit sanction types, reason and expiry.
2. Expose a reusable write-authorization predicate with current-time checks.
3. Test mute/ban behavior, expiry and restricted permanent sanctions.

**Scope:**

- `sanctions` table with kind, reason code, start, expiry and issued-by.
- Write-path enforcement for both sessions and agent tokens.
- Automatic expiry checked on each request, with no scheduler required.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Sanctions are checked before content work, so a banned identity cannot consume moderation budget.

This invariant and the acceptance cases belong to planned protected check `agora-048`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A muted identity can read but not post.
- [ ] An expired sanction no longer blocks and stays in the record.
- [ ] A sanction without an expiry is refused unless issued by an administrator.

**Test scenario:** Use a frozen-clock internal write-authorization adapter to assert mute/ban refusal, expiry and audit; 063 later checks every live write path.

## Out of scope

- IP bans.
- Permanent bans without an administrator.
