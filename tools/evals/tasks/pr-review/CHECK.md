# Check: pr-review

## Success

- Command: `head -1 ".aeion/reviews/$(git rev-parse HEAD).md"`
- Expected: `Review: OK` when nothing blocks, or no file at all when the review found a blocker
- Command: `git status --short`
- Expected: no change to a tracked file
- Human judgment: the review names concrete paths and lines, and a clean verdict is not a summary of the diff.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
