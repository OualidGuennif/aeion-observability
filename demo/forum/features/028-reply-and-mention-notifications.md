---
id: 028
sequence: 27
title: "Reply and mention notifications"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [022, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 028 — Reply and mention notifications

## Intent

Notify an author when someone replies to their post or names them, with a bounded inbox and no notification for hidden or moderated content.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add deduplicated reply/mention notification records.
2. Build a bounded inbox and recheck target visibility at read time.
3. Test repeated events, unknown handles and hidden/removed targets.

**Scope:**

- `notifications` table with recipient, kind, target and read flag.
- Generation on reply and on `@handle` mention, deduplicated per target.
- An inbox page with mark-all-read and a cap on unread items.
- Create notifications only for recipients still authorized to view the target; hide inaccessible targets on inbox reads too.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Mentions resolve against exact handles only; a mention never triggers a lookup that reveals whether a hidden account exists.

This invariant and the acceptance cases belong to planned protected check `agora-028`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A reply creates one notification, not one per render.
- [ ] Mentioning an unknown handle notifies nobody and stores nothing.
- [ ] A hidden reply creates no notification.

**Test scenario:** Reply, mention and hide; assert the notification rows before and after each action.

## Out of scope

- Push, email or websocket delivery.
- Mentions of non-existent handles creating accounts.
