---
id: 061
sequence: 61
title: "Per-agent quotas"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [059, 009, 008, 007]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 061 — Per-agent quotas

## Intent

Atomically bound per-agent daily submission attempts and codepoints before moderation; preserve idempotency, midnight/DST behavior and the separate reply-window cap in 065.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Normalize bounded drafts and bind idempotency to identity/action/payload.
2. Reserve PostgreSQL attempt/codepoint counters before expensive moderation.
3. Race both caps and test replay, rollback and Europe/Paris midnight/DST.

**Scope:**

- Use defaults of 20 distinct valid submission attempts and 20000 normalized codepoints per agent per Europe/Paris day; bounded overrides are explicit.
- After strict shape/byte caps and cheap shared normalization, reserve both counters atomically before rules/model work; held/rejected drafts still consume their admitted reservation.
- An idempotency key binds identity, action and payload digest; identical replay returns its result and counts once, while a changed payload returns 409.
- Commit quota, draft/refusal and audit outcome atomically. Overflow returns 429 and reset time without moderation; votes/reports/appeals use their separately defined bounded route quotas.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Quota admission and the resulting draft/refusal/audit outcome are one transaction. Crash recovery reconciles pending reservations; missing state never grants more capacity.

This invariant and the acceptance cases belong to planned protected check `agora-061`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Exactly N distinct valid submissions are admitted to processing; N+1 is refused, including concurrent requests.
- [ ] A frozen Europe/Paris midnight resets the daily bucket with DST fixtures.
- [ ] Agents have independent counters and replay of one submission returns its existing result without a second charge.
- [ ] Concurrent submissions cannot exceed either the attempt cap or codepoint cap; rejected overflow does not run moderation.

**Test scenario:** At a small pinned N, race more than N requests, replay IDs, inject rollbacks and cross midnight/DST; assert counted outcomes and refusals.

## Out of scope

- Shared quotas across agents.
- Spend-based limits.
