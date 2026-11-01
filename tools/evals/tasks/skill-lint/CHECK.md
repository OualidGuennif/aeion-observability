# Check: skill-lint

## Success

- Command: `tools/skills/lint; echo "exit=$?"`
- Expected: `PASS: 17 skills` then `exit=0`
- Command: `python3 tools/skills/tests/test_lint.py`
- Expected: exits 0 and reports a test that builds a bad fixture and sees exit 1
- Command: `tools/factory-tests`
- Expected: `factory-tests: PASS`, with `tools/skills/tests/test_lint.py` listed
- Human judgment: the failure message names the folder, not just the rule.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
