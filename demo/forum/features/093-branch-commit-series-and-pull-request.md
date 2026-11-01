---
id: 093
title: "Branch, commit series and pull request"
area: build
size: M
parallel: true
depends_on: [092]
owner: builder
status: proposed
---

# 093 — Branch, commit series and pull request

**Goal.** Publish a finished build as one branch, a commit series naming the feature id, and a pull request whose body carries the spec, the gate result and the trace link.

## Scope

- Branch naming by feature id and slug.
- A commit per coherent step, with the feature id in each subject.
- `gh pr create` with a generated body and a draft state until checks pass.

## Out of scope

- Merging, which belongs to the policy feature.
- Force-pushing over an existing branch.

## Acceptance

- [ ] The pull request exists, references the feature, and is a draft before checks.
- [ ] The body includes the gate verdict and a trace link.
- [ ] A build that changes nothing opens no pull request and says why.

## Security

The token used by `gh` is scoped to the repository and never printed; the commit author is the orchestrator identity.

## Test

Publish into a scratch repository and assert the branch, the commits and the body fields.
