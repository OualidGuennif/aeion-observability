---
id: 081
title: "Refresh from a local drop folder"
area: corpus
size: S
parallel: false
phase: P4
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [076, 009]
owner: builder
status: proposed
---

# 081 — Refresh from a local drop folder

## Intent

Pick up new corpus files dropped into a local folder on a schedule, so a human can add material without a deploy or a network path.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_e.py`.

## Inputs

- Confined regular-file drop folder with a processed checksum and bounded per-file size.
- Writers publish through atomic rename to .json; temporary files are ignored and the loader parses bytes from one opened descriptor.
- Reject symlinks, traversal and inode replacement; two stable checksums alone do not prove a file complete.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

## Invariants

Path resolution is confined to the folder; no traversal and no symlink following.

This invariant and the acceptance cases belong to planned protected check `agora-081`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A completed atomically renamed file produces one imported record across replay.
- [ ] Symlinks and out-of-root replacements are refused and audited.
- [ ] A partially written temporary file is ignored; only its completed renamed version is eligible.

**Test scenario:** Ignore partial temporary files, accept atomic .json rename once, race a symlink/inode replacement and assert confined-descriptor refusals and audit.

## Out of scope

- Uploads through the web interface.
- Remote sources.
