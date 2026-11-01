---
id: 092
title: "Workspace isolation per build"
area: build
size: M
parallel: true
depends_on: [091]
owner: builder
status: proposed
---

# 092 — Workspace isolation per build

**Goal.** Give every build its own worktree and scratch directory, so two builds cannot edit the same files or see each other's drafts.

## Scope

- A per-feature worktree created from the current `develop` head.
- A scratch directory with a fixed layout and cleanup on success.
- A refusal to reuse a worktree belonging to another feature.

## Out of scope

- Caching dependencies between builds.
- Sharing a workspace between parallel builds.

## Acceptance

- [ ] Two builds run at once and their diffs never overlap by accident.
- [ ] A leftover worktree from a crash is detected and named, not silently reused.
- [ ] Cleanup removes the worktree and keeps the branch.

## Security

The worktree lives outside the host's shared mount; the build never writes to the repository root.

## Test

Start two builds and assert distinct paths and diffs; crash one and assert the detection.
