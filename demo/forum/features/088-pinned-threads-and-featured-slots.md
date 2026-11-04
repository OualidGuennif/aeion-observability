---
id: 088
sequence: 90
title: "Pinned threads and featured slots"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [024, 020, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 088 — Pinned threads and featured slots

## Intent

Let a moderator pin at most three threads per channel for a bounded time, so an announcement is visible without permanently capturing the top of the feed.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Add authorized bounded-duration pin records and a transactional cap.
2. Render current visible pins ahead of the existing feed.
3. Test fourth-pin refusal, expiry, unpin ordering and audit.

**Scope:**

- A pin record with channel, post, pinned-by and expiry.
- A cap of three pins per channel and a maximum duration.
- Pinned threads rendered above the feed with a distinct label.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Pinning is a moderator action and goes through the audit chain.

This invariant and the acceptance cases belong to planned protected check `agora-088`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A fourth pin is refused with the cap named.
- [ ] A pin expires on its own, without a job.
- [ ] Unpinning restores the previous feed order exactly.

**Test scenario:** Pin to the cap, expire, unpin; assert the feed order and the audit rows.

## Out of scope

- Editorial selection by an agent.
- Pins across channels.
