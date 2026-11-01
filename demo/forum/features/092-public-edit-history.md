---
id: 092
title: "Public edit history"
area: forum
size: M
parallel: false
phase: P5
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [030, 014, 020]
owner: builder
status: proposed
---

# 092 — Public edit history

## Intent

Show that a post was edited and when, with the number of revisions, while keeping the diffs for moderators only.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_f.py`.

## Inputs

- A revision count and last-edit time rendered next to the author.
- A moderator view with the rendered diff per revision.
- A refusal to hide an edit by deleting the revision rows.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Revisions are append-only; the audit chain records each edit.

This invariant and the acceptance cases belong to planned protected check `agora-092`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

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
