# Task: pr-review

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/pr-review` from that commit

## Prompt (send this text unchanged)

> Review `origin/develop..HEAD` with the `pr-review` skill: find the defects that would survive a
> reading, not a list of everything the diff touches. Record the verdict where the pre-push gate
> reads it, for the exact commit, first line `Review: OK` only when nothing blocks. If something
> blocks, do not write a review file: report the finding and the fix instead.

## Scope

- In scope: `.aeion/reviews/<sha>.md` (git-ignored) and the report.
- Out of scope: the code under review, any commit rewrite, a push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
