# Task: changelog-line

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/changelog-line` from that commit

## Prompt (send this text unchanged)

> Add the `Unreleased` line for this change: `tools/evals/report` gains a `--since` filter. Follow
> the style of the existing entries in `CHANGELOG.md` (one sentence, verb first, no trailing period,
> wrapped like its neighbours) and touch nothing else. If the same fact already has a line, say so and
> change nothing.

## Scope

- In scope: `CHANGELOG.md`, one bullet under `## [Unreleased]`.
- Out of scope: code, `VERSION`, the task set, a commit, a push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
