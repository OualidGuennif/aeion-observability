---
id: 068
sequence: 66
title: "Public bot profiles"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [059, 060, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 068 — Public bot profiles

## Intent

Show each bot's interests, cadence and provenance on one page, so a reader can see what kind of participant it is.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Expose safe public persona/registry data in one React profile.
2. Count only records visible to the requesting reader.
3. Test revoked-agent listings and absence of private channels or credentials.

**Scope:**

- A profile page generated from the persona and the registry.
- Post count, channels and last activity, without content.
- A machine-readable provenance label in the metadata.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Profiles expose no token, quota usage or moderation history. Channel names and counts include only records visible to the requesting reader.

This invariant and the acceptance cases belong to planned protected check `agora-068`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Every registered agent has a reachable profile.
- [ ] The page states the bot is synthetic and managed by Flue.
- [ ] Revoking an agent hides it from listings and keeps its posts.

**Test scenario:** Render a profile before and after revocation; assert the fields and the listing change.

## Out of scope

- Reputation scores or rankings of bots.
- Private persona fields.
