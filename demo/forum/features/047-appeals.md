---
id: 047
sequence: 49
title: "Appeals"
area: moderation
size: M
parallel: false
phase: P2
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [046, 008, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 047 — Appeals

## Intent

Let an author appeal a decision once, with the reason code attached, and require a different moderator to decide, so a decision is checked rather than repeated.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Add one appeal per action with an independent deciding moderator.
2. Recompute current rules/access before an overturned appeal can restore.
3. Test duplicates, self-review and refusal of an engine-bypassing restoration.

**Scope:**

- `appeals` table linked to one moderation action and one author.
- A rule that the deciding moderator differs from the original one.
- Outcomes: upheld, overturned, or escalated to the administrator.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Appeals are rate limited per author and audited like any other action.

This invariant and the acceptance cases belong to planned protected check `agora-047`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A second appeal on the same action returns 409; the original moderator cannot decide their own appeal.
- [ ] Overturning recomputes current content/rules/object access and records its result atomically with audit; a formerly allowed item may now remain held.
- [ ] Only the separately authorized administrator override can restore against the current deterministic verdict; an ordinary appeal cannot bypass it.

**Test scenario:** Test duplicate appeals, self-review refusal, allowed restoration and a changed-rules fixture where overturning cannot publish against the current verdict.

## Out of scope

- Appeals against bans by non-authors.
- Multiple appeal rounds on the same action.
