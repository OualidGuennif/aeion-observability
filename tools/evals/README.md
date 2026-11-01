# Local evaluation harness

One append-only record per run, so a workflow change can be compared with what came before.
It measures the harness, not the model: no model call, no network, no dependency.

The three numbers, read from `report`:

- **Accepted changes**: successes divided by runs, per harness (the report's success rate).
- **Cost per accepted change**: total `cost_usd` divided by successes (both columns in the report).
- **Defects after done**: the sum of `defects_after_done`, the failures found once a task was called done.

The task set is `tools/evals/tasks/<task>/`, three short files:
`TASK.md` (the exact prompt, starting commit and scope), `CHECK.md` (the command or human judgment
that decides success and what counts as failure), `BASELINE.md` (the last known result, or
"not run yet"). `TEMPLATE/` holds empty forms to copy.

## Commands

```sh
tools/evals/record --task changelog-line --harness claude-code --success yes --minutes 12.5 \
  --model claude-sonnet-4-5 --tokens 48000 --cost-usd 0.42 --human-interventions 1 \
  --defects-after-done 0 --notes "first slice"
tools/evals/report            # markdown table, one row per harness plus All
tools/evals/report --json     # the same numbers as one JSON object
```

Unknown optional metrics remain unknown: if any run omits a metric, its aggregate is `N/A`
in the table and `null` in JSON. Explicit zero remains zero. The reader rejects invalid
required fields, timestamps, types, negative numbers and non-finite values with a line number.
For before/after comparisons, use separate `--file` datasets with matched tasks and recorded
baseline commits; rows group by harness, not by task or version.

`changelog-line` above is one of the shipped tasks; the rest sit beside it in `tools/evals/tasks/`,
eleven still at the "not run yet" baseline; `architecture-answer` records one Pi run.
One record line looks like this (`--dry-run` prints it
without writing):

```json
{"task":"changelog-line","harness":"claude-code","success":true,"minutes":12.5,"factory":"1.7.0","recorded_at":"2026-10-31T09:12:44Z"}
```

Records go to `tools/evals/results.jsonl` (git-ignored, resolved from the repository root);
`--file` takes another path, absolute or from the root. `--dry-run` prints the record and writes
nothing. The record shape is `schema.json`; a bad input exits 2 and writes nothing.

## Limits

- Self-reported: the person who ran the task fills the numbers in.
- Small samples: three runs of one task say little; treat a difference under a run or two as noise.
- No model calls and no sandbox: this tool records, it does not execute or verify the work.
- Not a public benchmark: the task set is local, comparable only inside this factory.
