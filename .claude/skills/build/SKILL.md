---
name: build
description: Implements an approved plan in thin, tested slices, letting language-server diagnostics and the edit hooks speak after every edit, and committing each green slice. Use when implementing a planned change.
---

# Build

## Overview
Thin vertical slices: each one compiles, passes its tests and is committed. Rules: `knowledge/policies/engineering.md`.

## When to use
After `plan` (and `spec` when behaviour changes). Not before a yes.

## Process
1. Under git, inspect the current branch/worktree and work on the owner-approved branch.
   A branch switch or pull must preserve existing work; do not perform either blindly.
2. Pick the smallest slice that moves toward the plan; write its test first when practical.
3. Edit; read the diagnostics and hook output after each edit; fix before moving on.
4. Run the slice's tests and add its `CHANGELOG.md` line. Commit with a what/why message
   only when a commit is included in the owner-authorized workflow.
5. Repeat. Stop and re-plan if the plan turns out wrong.

## Rationalizations
| Excuse | Rebuttal |
| --- | --- |
| "I'll run the tests at the end" | Then one failure hides behind ten changes. |
| "This helper will be useful later" | No abstraction without two real users. |

## Red flags
A commit with failing tests; a slice touching ten files; silenced diagnostics.

## Verification
- [ ] Every commit passed the pre-commit and its tests.
- [ ] The diff contains only what the plan named.

## Protect the working state
Inspect branch, dirty files and existing task work before a switch, pull, merge or commit.
Do not auto-pull into someone else's active checkout, discard changes or treat local edit
approval as permission to push. If the owner requested local develop edits, stay on develop
and leave a reviewable diff; commit only when included in the authorized workflow.

Trace interface compatibility and failure handling through the slice. Prefer an existing
helper when it already owns the behavior, and make state transitions explicit. Validate a
slice before broadening it. A test/build failure is evidence to diagnose, not permission to
weaken checks or replace dependencies. A changed plan waits at the actual decision boundary.
