# Check: handover

## Success

- Command: `grep -n '^## ' work/handovers/session-<id>.md`
- Expected: exactly five headings, in the order Scope, Completed, Remaining, Constraints, Evidence
- Command: `git status --short --ignored --untracked-files=all -- work/handovers/session-<id>.md`
- Expected: one ignored file (`!!`) at that path; handovers remain local recovery state
- Command: `git status --short`
- Expected: unchanged from the starting state, because `work/handovers/` is ignored
- Human judgment: every claim in Completed points at a path that exists, and Remaining is not empty.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
