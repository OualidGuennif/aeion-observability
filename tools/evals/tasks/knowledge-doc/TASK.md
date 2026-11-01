# Task: knowledge-doc

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/knowledge-doc` from that commit

## Prompt (send this text unchanged)

> Write `knowledge/components/local-evaluation.md`, a component spec for `tools/evals/`: what
> `record` and `report` do, the three numbers they produce, the task-folder contract, and the limits
> (self-reported, small samples, no model calls, not a public benchmark). Use the front matter shape
> of `knowledge/components/factory-architecture.md`, declare `tools/evals/` as a source, add the
> document to `knowledge/components/index.md`, and link it from `knowledge/operations/evals.md`.
> Do not restate rules that `knowledge/operations/evals.md` already owns; link to it instead.

## Scope

- In scope: `knowledge/components/local-evaluation.md`, `knowledge/components/index.md`, `knowledge/operations/evals.md`, `CHANGELOG.md`.
- Out of scope: `tools/evals/` itself, the runbook's rules, any dependency, any push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
