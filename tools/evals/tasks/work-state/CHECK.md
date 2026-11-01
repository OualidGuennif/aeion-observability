# Check: work-state

## Success

- Command: `tools/repo-health/repo-health`
- Expected: `work/current.md` at or under 150 lines, exit 0
- Command: `grep -c '^- ' work/current.md`
- Expected: the entry still has its five lines, in the documented order
- Command: `git diff --name-only`
- Expected: exactly `work/current.md`
- Human judgment: the status word matches what is really true, and `Next:` names who acts.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
