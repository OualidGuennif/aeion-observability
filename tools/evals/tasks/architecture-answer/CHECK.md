# Check: architecture-answer

## Success

- Command: `tools/architecture/ask deps tools/evals/record` and `tools/architecture/ask tests tools/evals/record`
- Expected: both exit 0, and every path the answer cites exists
- Command: `git status --short`
- Expected: empty
- Human judgment: the answer separates what the graph knew before this run from what it cannot see.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
