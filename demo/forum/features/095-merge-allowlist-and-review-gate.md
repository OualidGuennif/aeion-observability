---
id: 095
title: "Merge allowlist and review gate"
area: build
size: M
parallel: true
depends_on: [094]
owner: builder
status: proposed
---

# 095 — Merge allowlist and review gate

**Goal.** Merge automatically only inside an allowlisted path set with a green verdict and a recorded review; everything else waits for the owner.

## Scope

- An allowlist of paths an agent may merge, checked file by file.
- A review gate that reads the diff and the verdict and writes an approval or a refusal.
- A hard refusal for workflows, migrations, deploy files, secrets and the security surface.

## Out of scope

- Changing branch protection.
- Merging into `main`.

## Acceptance

- [ ] A diff touching `.github/` is never auto-merged, even when green.
- [ ] A green diff wholly inside the allowlist merges and records the sha.
- [ ] A refused merge leaves the branch and says what blocked it.

## Security

This is the boundary that keeps autonomy from becoming unbounded privilege; it is tested negatively first.

## Test

Run three diffs — allowed, outside the allowlist, mixed — and assert merge, refusal, refusal.
