---
id: 028
title: "Reply and mention notifications"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [022, 020]
owner: builder
status: proposed
---

# 028 — Reply and mention notifications

## Intent

Notify an author when someone replies to their post or names them, with a bounded inbox and no notification for hidden or moderated content.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

- `notifications` table with recipient, kind, target and read flag.
- Generation on reply and on `@handle` mention, deduplicated per target.
- An inbox page with mark-all-read and a cap on unread items.
- Create notifications only for recipients still authorized to view the target; hide inaccessible targets on inbox reads too.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Mentions resolve against exact handles only; a mention never triggers a lookup that reveals whether a hidden account exists.

This invariant and the acceptance cases belong to planned protected check `agora-028`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
