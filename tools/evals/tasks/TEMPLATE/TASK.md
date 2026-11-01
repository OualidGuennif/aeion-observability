# Task: <slug>

Copy this folder to `tools/evals/tasks/<slug>/`, then replace every `<...>`.

## Starting point

- Commit: `<sha of develop or the release tag>`
- Factory: `<VERSION>`
- Branch: `task/<slug>` from `<starting commit>`

## Prompt (send this text unchanged)

> <The exact prompt an owner would give, including the files it may touch.>

## Scope

- In scope: `<what the run may change>`
- Out of scope: `<what must not change>`

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
