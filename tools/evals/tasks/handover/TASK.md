# Task: handover

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/handover` from that commit

## Prompt (send this text unchanged)

> A session is about to close at its context limit. From this transcript and the current worktree,
> write `work/handovers/session-<id>.md` using the exact headings and order that
> `tools/context/budget.py` requires, five sections, each holding facts and paths rather than
> narrative. Nothing in the repository changes except that file. Do not invent a completed item, and
> name every unresolved limit explicitly.

## Scope

- In scope: one new file under `work/handovers/`.
- Out of scope: `work/current.md`, any source file, a commit, a push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
