# Baseline: architecture-answer

One block per measured run, newest first. "not run yet" is a valid baseline.

## 2026-10-31 — pi

- Factory: `1.7.0`, commit `df4d421`
- Model: `deepseek-v4.1-flash`, `--thinking max`
- Result: `yes`; `CHECK.md` said both queries exit 0, every cited path exists and the tree stayed clean
- Cost: not metered (subscription); 0.9 minutes
- Minutes: `0.9`
- Human interventions: `0`; rework commits: `0`; defects after done: `0`
- Notes: correct `deps` and `tests` edges, and honest blind spots on both sides; two cited line
  numbers were off by one, which the check caught before acceptance.

## not run yet

No record exists for another harness; `tools/evals/report` lists only the run above.
