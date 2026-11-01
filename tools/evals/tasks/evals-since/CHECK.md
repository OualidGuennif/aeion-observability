# Check: evals-since

## Success

- Command: `python3 tools/evals/tests/test_evals.py`
- Expected: exits 0, with at least three cases naming `since`
- Command: `tools/evals/report --since 2026-13-01; echo "exit=$?"`
- Expected: a message naming the bad date, then `exit=2`
- Command: `tools/evals/report` on a file with three dated records, one older than `--since`
- Expected: the older record's task does not appear
- Human judgment: an undated record is refused, not silently dropped.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
