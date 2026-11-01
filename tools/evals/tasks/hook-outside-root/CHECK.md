# Check: hook-outside-root

## Success

- Command: `python3 tools/agents/tests/test_hooks.py`
- Expected: exits 0, with a case whose name names the outside-root edit
- Command: `git diff --stat 26f19e0`
- Expected: only `tools/agents/tests/test_hooks.py`
- Human judgment: the report says the mutation was tried, and the case failed while it was in place.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
