# Check: evals-p90

## Success

- Command: `python3 tools/evals/tests/test_evals.py`
- Expected: exits 0, with a case asserting 100 for 10, 20, 30, 40, 100
- Command: `tools/evals/report --json` on that fixture
- Expected: `p90_minutes` present and equal to the case's value
- Expected: the Markdown header row contains `p90 min`
- Human judgment: the number is the same in the table, the JSON and the `All` row.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
