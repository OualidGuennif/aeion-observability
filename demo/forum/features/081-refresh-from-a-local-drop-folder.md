---
id: 081
title: "Refresh from a local drop folder"
area: corpus
size: S
parallel: false
depends_on: [076]
owner: builder
status: proposed
---

# 081 — Refresh from a local drop folder

**Goal.** Pick up new corpus files dropped into a local folder on a schedule, so a human can add material without a deploy or a network path.

## Scope

- A watched directory, a processed marker and a per-file checksum.
- One run picks up new files only and reports counts.
- A refusal to follow a symlink or read outside the folder.

## Out of scope

- Uploads through the web interface.
- Remote sources.

## Acceptance

- [ ] A new file is loaded exactly once.
- [ ] A symlink in the drop folder is refused and audited.
- [ ] A partially written file is skipped until its checksum matches on a later run.

## Security

Path resolution is confined to the folder; no traversal and no symlink following.

## Test

Drop two files, add a symlink, and re-run; assert the counts and the refusal.
