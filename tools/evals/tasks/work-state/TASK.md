# Task: work-state

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/work-state` from that commit

## Prompt (send this text unchanged)

> The golden task set now has its twelve folders and no baseline. Replace its `BACKLOG` entry in
> `work/current.md` with the state that matches, keeping the required lines (`- Owner decision:`,
> `- State:`, `- Next:` with who, `- Blocker:`, `- Evidence:`) and the 150-line cap. Do not add a
> second entry for the same work and do not delete an unrelated one.

## Scope

- In scope: one entry in `work/current.md`.
- Out of scope: every other file, a commit, a push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
