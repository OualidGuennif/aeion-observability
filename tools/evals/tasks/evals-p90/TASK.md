# Task: evals-p90

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/evals-p90` from that commit

## Prompt (send this text unchanged)

> Add a `p90 min` column to `tools/evals/report`, before the median column, using nearest-rank
> percentile over the `minutes` values: sort, index `ceil(0.9 * n) - 1`, one decimal. It appears in
> the Markdown table, in `--json` as `p90_minutes`, and in the `All` row. Add cases to
> `tools/evals/tests/test_evals.py` for one value, five values (10, 20, 30, 40, 100 gives 100), and
> ten values. Document the column in `tools/evals/README.md` and one `Unreleased` line.

## Scope

- In scope: `tools/evals/report`, `tools/evals/tests/test_evals.py`, `tools/evals/README.md`, `CHANGELOG.md`.
- Out of scope: `record`, the task set, `knowledge/operations/evals.md` (the runbook keeps the three numbers), any dependency, any push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
