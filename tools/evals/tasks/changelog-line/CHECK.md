# Check: changelog-line

## Success

- Command: `git diff --name-only`
- Expected: exactly `CHANGELOG.md`
- Command: `sed -n '/## \[Unreleased\]/,/## \[1/p' CHANGELOG.md | head -6`
- Expected: the new bullet sits under `## [Unreleased]`, in the same style as its neighbours
- Human judgment: the line says what a user gains, not which file changed.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
