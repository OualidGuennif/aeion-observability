# Check: <slug>

Copy this folder to `tools/evals/tasks/<slug>/` and name the decision, never reword it mid-run.

## Success

- Command: `<one command, or "human judgment">`
- Expected: `<exit 0, or the exact output an owner would accept>`
- Human judgment: `<what an owner reads when no command decides it>`

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
