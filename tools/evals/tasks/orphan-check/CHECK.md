# Check: orphan-check

## Success

- Command: `tools/knowledge/knowledge-check; echo "exit=$?"`
- Expected: `RESULT: PASS (0 problem(s))` and `exit=0` on this repository, with the new rule active
- Command: `python3 tools/knowledge/tests/test_knowledge_check.py`
- Expected: exits 0, and the new case names are visible in the output
- Human judgment: the fixture is a real document with front matter, not an empty file.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
