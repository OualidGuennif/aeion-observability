---
id: 092
sequence: 94
title: "Public edit history"
area: forum
size: M
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [030, 014, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 092 — Public edit history

## Intent

Show that a post was edited and when, with the number of revisions, while keeping the diffs for moderators only.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

**Delivery steps:**

1. Expose edit count/time from existing retained revision records.
2. Add authorized moderator diffs without a public content-history API.
3. Edit/delete fixtures and prove markers, privacy and surviving tombstones.

**Scope:**

- A revision count and last-edit time rendered next to the author.
- A moderator view with the rendered diff per revision.
- A refusal to hide an edit by deleting the revision rows.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Revisions are append-only; the audit chain records each edit.

This invariant and the acceptance cases belong to planned protected check `agora-092`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An edited post states the number of revisions and the time.
- [ ] An unedited post shows no marker.
- [ ] The revision rows survive a post deletion as tombstones.

**Test scenario:** Edit twice and delete; assert the marker, the moderator diffs and the surviving rows.

## Out of scope

- Public diffs.
- Editing after a moderation action.
