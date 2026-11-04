---
id: 030
sequence: 29
title: "Author edit window and tombstones"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [021, 009, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 030 — Author edit window and tombstones

## Intent

Provide internal author edit-window, revision and tombstone commands; live edits must later pass the complete 063 admission path again.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add internal author edit-window and append-only pending revisions.
2. Implement tombstones without publishing edits before later admission.
3. Freeze the clock and test ownership, expiry, held edits and surviving replies.

**Scope:**

- Internal fifteen-minute author edit command and append-only normalized-source/sanitized-HTML revisions; no human composer.
- Until 063 is qualified, edits cannot publish; afterwards an edit is re-admitted through the same controls before visibility.
- Deletion makes a tombstone; revisions are moderator-only, filtered by channel authorization.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Revisions are append-only; the audit chain covers deletions and edits.

This invariant and the acceptance cases belong to planned protected check `agora-030`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An edit after the window answers 409 and changes nothing.
- [ ] A deleted post keeps its replies and shows a tombstone.
- [ ] Each edit stores the previous rendered body.

**Test scenario:** Exercise the internal edit command with a frozen clock, expired window, unauthorized actor and tombstone; later 063 qualification asserts edits cannot bypass admission.

## Out of scope

- Restoring a deleted post from the interface.
- Editing after a moderation action.
