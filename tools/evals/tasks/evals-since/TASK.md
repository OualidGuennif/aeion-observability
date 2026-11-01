# Task: evals-since

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/evals-since` from that commit

## Prompt (send this text unchanged)

> Add `--since YYYY-MM-DD` to `tools/evals/report`: it keeps only records whose `recorded_at` date is
> on or after that day, UTC, and combines with `--json`. A malformed date, or a record without
> `recorded_at`, exits 2 and names the line. Without `--since` nothing changes. Add the cases to
> `tools/evals/tests/test_evals.py`, document the flag in `tools/evals/README.md` and
> `knowledge/operations/evals.md`, and add one `Unreleased` line.

## Scope

- In scope: `tools/evals/report`, `tools/evals/tests/test_evals.py`, `tools/evals/README.md`, `knowledge/operations/evals.md`, `CHANGELOG.md`.
- Out of scope: `record`, `schema.json`, the task set, any dependency, any push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
