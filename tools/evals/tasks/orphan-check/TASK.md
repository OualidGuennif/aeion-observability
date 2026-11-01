# Task: orphan-check

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/orphan-check` from that commit

## Prompt (send this text unchanged)

> Make `tools/knowledge/knowledge-check` fail on an orphan: a file under `knowledge/` that no other
> file under `knowledge/` links to, directly or through an index it is listed in. Report it as
> `FAIL <path>: orphan, link it from knowledge/index.md or a folder index`, one line per orphan, and
> keep the existing rules and exit codes unchanged. Add a test to
> `tools/knowledge/tests/test_knowledge_check.py` that builds an unlinked document in a temporary
> root and expects that failure, and one that links it and expects none. Add one `Unreleased` line.

## Scope

- In scope: `tools/knowledge/knowledge-check`, its test file, `CHANGELOG.md`.
- Out of scope: deleting or moving any existing knowledge document, `doc-links`, any dependency, any push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
