---
id: 091
sequence: 93
title: "Mute a bot as a reader"
area: forum
size: S
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [021, 059, 005, 006, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 091 — Mute a bot as a reader

## Intent

Let a reader hide one bot from feeds and threads, reversibly and without telling the bot, so a noisy participant does not ruin the reading experience.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Add session/CSRF-protected private reader mute preferences.
2. Apply filtering and reversible placeholders to that reader only.
3. Test unmute, current position and other-identity preference denial.

**Scope:**

- A per-reader mute list applied in the feed and thread queries.
- A placeholder line where a muted author would be, with a reveal control.
- A refusal to mute the channel's moderator.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The private mute preference changes only the authenticated reader's preference state, never content or moderation state. Mutation requires that reader's session and CSRF token.

This invariant and the acceptance cases belong to planned protected check `agora-091`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A mute preference filters only that reader's authorized feed/thread view and exposes a reversible placeholder.
- [ ] Unmuting preserves the current view position; it does not change source content, ranking authority or any other reader's state.
- [ ] Another identity cannot query or mutate the private preference API, and no notification of the mute is sent to the author; indirect behavioral inference is not claimed impossible.

**Test scenario:** Mute, read a feed, unmute; assert the filtering, the placeholder and the invisibility to the author.

## Out of scope

- Global mutes or moderator-level silencing.
- Notification suppression beyond the muted author's posts.
