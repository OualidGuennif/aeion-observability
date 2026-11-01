---
name: pr-review
description: Reviews a diff or pull request using concrete failure evidence and a bounded finding list. Use for requested local review, before a develop push or release; never creates reviewer agents automatically.
---

# Review a change

## Overview
Independent review and a local self-assessment are different evidence. One verdict per exact target. Flow: `knowledge/policies/engineering.md`.

## Process
Two targets, same review. **Develop push:** the range `origin/develop..HEAD` (`git log`, `git diff`).
**Release:** the pull request `develop → main` (`gh pr view <n>`, `gh pr diff <n>`, `gh pr checks <n>`).
1. Name the target: local changes (including untracked files), an exact commit range or a PR head.
   Read [the review checklist](references/review-checklist.md) and the touched contracts/callers/tests.
2. Review in the current context by default. An agent profile from the pool is optional reading,
   not permission to spawn a reviewer. If an independent reviewer is explicitly authorized and
   available, give it the target, project rules and relevant docs without seeding intended findings.
   Without that independent pass, label the result a local assessment; do not issue the formal
   `Review: OK` receipt required by the existing push gate. Never simulate independence.
3. A sensitive diff: also skill `security-scan` on the changes, or say it was not run.
4. Verify every finding yourself; drop what you cannot confirm.
   Trace suggestions against the code/spec before implementing them; disagree with an unsupported
   fix. For context/architecture work, verify claimed guarantees and exact-SHA artifact coverage.
5. For an authorized formal review with the required independent pass, write the verdict, first line exactly `Review: OK` or `Review: NOT OK`:
   ```
   Review: OK            (or)   Review: NOT OK
   - <high|medium|low> path:line -- the finding (at most five)
   Checks: CI <state or "not run (develop)">; doc-links <result>; tests <what ran>
   ```
   - Develop push: save it as `.aeion/reviews/<full HEAD sha>.md` (ignored; `tools/git-hooks/pre-push`
     reads it), then after the push post it on the commit:
     `gh api repos/{owner}/{repo}/commits/<sha>/comments -F body=@.aeion/reviews/<sha>.md`.
   - Release: save it as `.aeion/loop-bodies/review-<n>.md` (the only body path read-only loops may
     publish) and `gh pr comment <n> --body-file .aeion/loop-bodies/review-<n>.md`.
   - Loop pull request into `develop`: as a release, on the PR; it merges after Review OK and a green CI.
6. NOT OK: fix, commit, review again; a new commit needs a new verdict. Release OK and CI green: the
   skill `ship` merges. A human decision waits before the merge; a deploy after it.

## Rationalizations
| Excuse | Rebuttal |
| --- | --- |
| "I wrote it, I know it's fine" | That is why the reviewer is fresh. |

## Red flags
Approving through the forge's review API; merging on red CI; a secret in a comment.

## Finding contract
Every finding needs an exact location, reachable trigger, consequence and analysis of existing guards.
Zero findings is valid. Use the checklist to reject speculative nits and generic thresholds.
No model is imposed; no upstream tool grant or mandatory delegation is inherited.
Publishing a review or changing forge state still needs the task's authorization.

## Verification
- [ ] The verdict is recorded for the exact commit (develop) or on the PR (release), with the checks line.
