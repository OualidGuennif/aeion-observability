# Check: skill-route

## Success

- Command: test -f the quoted skill path and the two documents
- Expected: all three paths exist
- Command: the quoted `AGENTS.md` line
- Expected: it is in the load-by-task table and names that same area
- Human judgment: the rejection of the two neighbours rests on their description, not on a guess.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
