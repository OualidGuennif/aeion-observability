# Task: skill-lint

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/skill-lint` from that commit

## Prompt (send this text unchanged)

> Add `tools/skills/lint`, a deterministic check over the 17 native skills in `.agents/skills/`.
> For every `SKILL.md` it fails when: the YAML front matter lacks `name` or `description`; `name`
> differs from the folder name; the description is longer than 1024 characters; the body after the
> front matter exceeds 150 lines; or a second skill declares the same `name`. Print one line per
> violation naming the folder and exit 1; print `PASS: <n> skills` and exit 0 when clean. Add
> `tools/skills/tests/test_lint.py` with at least one failing fixture built in a temporary folder,
> add the lint and its tests to `tools/factory-tests`, and add one `Unreleased` line to `CHANGELOG.md`.

## Scope

- In scope: `tools/skills/lint`, `tools/skills/tests/test_lint.py`, `tools/factory-tests`, `CHANGELOG.md`, and one line in `knowledge/operations/build-and-test.md`.
- Out of scope: editing the 17 skills, the pool, any adapter, any dependency, any push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
