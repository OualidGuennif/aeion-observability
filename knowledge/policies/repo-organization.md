---
type: Policy
title: "Repository organization"
description: "Top-level folders named by role, one home per concern, nothing generated in the tree, and how to move a folder safely."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: guide
    resource: ../../efficiency/1-quarks.md
    title: "Phase 1 of the guide"
---

# Repository organization

- **At most seven to nine top-level folders, named by role** (`apps/` or `services/`, `packages/`
  or `libs/`, `infra/`, `knowledge/`, `tools/`, `work/`); never after a version (`v2/`, `new/`).
- **One home per concern:** one repository map (in `AGENTS.md`), one place for runbooks, one for
  scripts, one copy of each rule. The `README.md` is for humans, about forty lines.
- **Nothing generated is tracked:** build outputs, caches, compiled files, editor metadata.
- **English names, by what a thing does.**
- **A move is one pull request** that updates every reference: build files, container contexts,
  CI, deploy scripts, docs, hooks, skills, and absolute paths on servers. A runtime path ships
  with a deploy.
- **Delete before you add:** stale reports, duplicated maps, dead pointers.
