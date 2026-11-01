---
type: Runbook
title: "Local evaluation harness"
description: "One appended record per run, a report of three numbers, and the task folder that makes runs comparable. Self-reported, local, no model calls."
status: draft
review_after: 2027-01-29
generated:
  by: aeion-factory/1.7
  at: 2026-10-31
sources:
  - id: record
    resource: ../../tools/evals/record
    title: "Append one record"
  - id: report
    resource: ../../tools/evals/report
    title: "The per-harness report"
  - id: schema
    resource: ../../tools/evals/schema.json
    title: "The record schema"
  - id: readme
    resource: ../../tools/evals/README.md
    title: "Usage and limits"
  - id: tests
    resource: ../../tools/evals/tests/test_evals.py
    title: "Fixture tests"
  - id: template
    resource: ../../tools/evals/tasks/TEMPLATE/TASK.md
    title: "The task folder template"
---

# Local evaluation harness

A workflow change (a new hook, a shorter skill, a different handover) needs a baseline, or
nobody can tell whether it helped. This harness records one line per run and reports the same
three numbers for every harness, so a change is compared with what came before instead of with
an opinion. It records; it does not run an agent, call a provider or reach the network.

## The measurement loop

1. Copy `tools/evals/tasks/TEMPLATE/` to `tools/evals/tasks/<slug>/` and fill the three files.
2. Run the task on one harness from the starting commit named in `TASK.md`.
3. Decide with `CHECK.md`, then `tools/evals/record` the outcome.
4. `tools/evals/report` shows the harness rows and the `All` row.
5. Change one thing in the factory, run the same task again, and compare the rows.

## The two commands

```sh
tools/evals/record --task <slug> --harness <slug> --success yes|no --minutes <float> \
  [--model TEXT] [--tokens INT] [--cost-usd FLOAT] [--human-interventions INT] \
  [--rework-commits INT] [--defects-after-done INT] [--notes TEXT] [--file PATH] [--dry-run]
tools/evals/report [--file PATH] [--json]
```

`record` appends one compact JSON object to `tools/evals/results.jsonl` (git-ignored, resolved from
the repository root, not the current directory), adds `recorded_at` in UTC with a `Z` suffix, and
takes `factory` from `VERSION` unless given. An invalid slug, a `--success` other than `yes`/`no`,
a negative number, a non-finite number (`nan`, `inf`) or a missing required flag exits 2 and writes
nothing. `--dry-run` prints the record and writes nothing.
Appending also separates an existing final record that has no trailing newline; its bytes are preserved.

`report` validates the required record fields, slug and string fields, timezone-aware timestamps,
non-negative finite numbers and integer counters before aggregating; an invalid row exits 2 with
its line number. Optional fields may be absent, but an explicit null or a wrong type is invalid.
It reads the file skipping blank lines, groups by `harness` and prints one Markdown table with
an `All` row: runs, successes, success rate as integer percent, median `minutes` to one decimal,
total `cost_usd` to two decimals, the sums of `human_interventions` and `defects_after_done`.
An optional total is unknown if any contributing run omits it: the table shows `N/A` and JSON
uses `null`. Explicit zero remains zero; incomplete totals are never presented as complete.
A malformed line exits 2 and names its line number; a
missing file exits 2 rather than reporting an empty result. `--json` prints one object with
`harnesses` and `all`; an empty file prints `No evaluation records.` (except with `--json`, which
keeps its shape). The record shape is [schema.json](../../tools/evals/schema.json).

For before/after comparisons, record matched tasks into separate `--file` datasets and label
their baseline commits. The report groups only by harness; mixing versions or task sets in one
file does not establish a performance improvement. No stored record is rewritten by reporting.

## The task set

One folder per task under `tools/evals/tasks/`, three short files:
[TASK.md](../../tools/evals/tasks/TEMPLATE/TASK.md) is the exact prompt an owner would give plus the
starting commit and scope; `CHECK.md` is the command or human judgment that decides success and what
counts as failure; `BASELINE.md` holds the last known date, harness, model, result, cost, minutes and
notes, where "not run yet" is a valid baseline. `TEMPLATE/` holds the empty forms; the shipped tasks
are the recurring shapes of work in this repository, each with the gate that decides it, and the owner
adds one, with its brief, when a new shape appears.

## The three numbers

- **Accepted changes**: successes ÷ runs per harness - did the work pass `CHECK.md` at all.
- **Cost per accepted change**: total `cost_usd` (or total `minutes`) ÷ successes - what one useful
  result cost, not what one attempt cost.
- **Defects after done**: the sum of `defects_after_done` - failures found once the run reported done.

Read them together: a cheaper harness that needs rework is not cheaper. The count of
`human_interventions` explains a suspiciously fast row.

## Limits

- Self-reported: whoever ran the task fills the numbers in, and nothing verifies them.
- Small samples: one or two runs per task are noise, not a trend.
- No model calls, no sandbox: the tool records and reports; it does not execute or grade the work.
- Local, not public: the task set is comparable inside this factory only, and changes to it reset
  the baseline.
- Usage and examples: [tools/evals/README.md](../../tools/evals/README.md).
