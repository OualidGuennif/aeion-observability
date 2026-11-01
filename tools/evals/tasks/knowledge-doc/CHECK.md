# Check: knowledge-doc

## Success

- Command: `tools/knowledge/knowledge-check; echo "exit=$?"`
- Expected: `RESULT: PASS (0 problem(s))` and `exit=0`
- Command: `tools/knowledge/doc-links`
- Expected: `RESULT: PASS`
- Command: `tools/knowledge/doc-links --for tools/evals/record`
- Expected: prints `knowledge/components/local-evaluation.md`
- Human judgment: a reader who opens only this file can say what a record is and what it cannot prove.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
