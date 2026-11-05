---
name: ship
description: Cuts a release from develop to main behind a review and a green CI, tags it and publishes its notes, then deploys only through the project's guards. Use when develop is ready to release, or when a release pull request has Review OK and green CI.
---

# Ship

## Process
1. On `develop`, pushed with `Review: OK`: `tools/release/release <major|minor|patch>` bumps `VERSION`
   and dates the `Unreleased` lines of `CHANGELOG.md`; commit, review (skill `pr-review`), push.
2. `gh pr create --base main --head develop --title "Release vX.Y.Z"` with the printed body; skill
   `pr-review` on it; wait for a green `gh pr checks`.
3. Release gate: skill `security-scan` on the changes since the last tag, `tools/knowledge/doc-links`.
4. `gh pr merge <n> --merge` (a merge commit: `develop` stays an ancestor of `main`; never squash a release).
   Wait for the `Architecture refresh` workflow to pass on the exact merged main SHA. A failed round is
   retried/corrected, never skipped.
5. Tag and publish: `git fetch origin`, `git tag -a vX.Y.Z origin/main -m vX.Y.Z`, `git push origin vX.Y.Z`,
   `gh release create vX.Y.Z --notes "$(tools/release/release --notes X.Y.Z)"`. The release name is exactly
   `vX.Y.Z` (no sentence, no summary) and the body is that section unedited, like the first releases. The
   source archives leave out `demo/` (`.gitattributes` export-ignore):
   `git archive vX.Y.Z | tar -t | grep -c '^demo/'` prints 0.
6. Catch `develop` up: `git switch develop && git merge --ff-only origin/main && git push` (the pre-push
   hook accepts commits already on `main`). Fast-forward local `main` too.
7. Deploy only through the project's deploy procedure and its guards, with a human's go when the project
   requires it; afterwards read the result through the read-only path and record it in `work/current.md`.
Without git: steps 1 and 7 only; the version lives in `VERSION` and `CHANGELOG.md`.

## Red flags
A squash-merged release; a tag on a commit other than the merged main; a deploy from an unmerged branch; a skipped CI run at the deployed commit; no rollback plan.

## Verification
- [ ] The deployed commit has a green CI run.
- [ ] The rollback command is known before the deploy.

## Bind the release to explicit authority
Before a push, merge, published release or deployment, confirm that the owner's current scope
authorizes that action; a plan, green checks or local branch edits alone are insufficient.
Prepare exact artifacts and validation before any missing approval is requested. For an
authorized release verify the reviewed head still matches, handle a changed head by re-review,
and identify compatibility/migration recovery before applying state changes.
