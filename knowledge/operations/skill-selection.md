---
type: Reference
title: "Native skills and passive source guidance"
description: "Native-first skill selection, selective enrichment and the boundary between a role document and an authorized agent execution."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/local-skill-maintenance
  at: 2026-10-31
sources:
  - resource: ../../.claude/skills/
    title: "Maintained native definitions"
  - resource: ../../tools/skills/annotations.json
    title: "Exact-source-bound scanner annotations"
  - resource: ../../tools/skills/pool.py
    title: "Deterministic pool inventory and search"
  - resource: ../../tools/skills/lint
    title: "Native skill front matter, trigger and body-size gate"
  - resource: ../../.agents/skills/
    title: "Shared discovery links"
---

# Native skills and passive source guidance

Æion Factory keeps its sixteen task skills and adds one selector, `skill-route`.
It does not activate a second skill framework or register a source library globally.
The [selector](../../.claude/skills/skill-route/SKILL.md) gives native guidance priority;
copied source material supplies a concrete missing technique only when useful.

## Optional workspace library

The project-local `skills/` library indexes canonical definitions from ECC, Addy Osmani's agent-skills, Anthropic's
official plugins and knowledge-work-plugins. Skill folders are directly under
`skills/`; agent Markdown definitions are under `skills/agents/`. The pool contains real versioned files and resources, not source symlinks. Metadata search
returns a small candidate list before any full definition is read. Reading, searching
and integrity checks require neither third-party source copies nor the lifecycle folder. If the optional source copies are absent, native Factory tasks continue to work.

Read the lifecycle pool policy before using a candidate. Only one relevant technique
and genuinely distinct specialist guidance belong in the task context. Neither a
raw source instruction nor a profile's `model`, `tools` or delegation fields grant
authority. A role document is optional reading, not a request to create an agent.
No source-derived generic size, coverage or confidence threshold becomes a gate.

## Native review and authority

The [review checklist](../../.claude/skills/pr-review/references/review-checklist.md)
requires a reachable failure scenario, exact location and existing-defense analysis;
it allows zero findings. Review in the current context by default. An independent
review pass may be used only with actual authorization and available tooling; a
local self-assessment cannot masquerade as that pass or create a formal push-gate
receipt. Existing exact-commit gate mechanics remain unchanged.

`security-scan` separates a manual boundary review from an actual scanner result.
Native-only proprietary plugins remain native-only; absent tools are coverage
limits. Installing a plugin, sending source to an external scanner and publishing
findings each keep their own authorization boundary.

## The native set, linted

`tools/skills/lint` checks every folder under `.agents/skills/` that holds a `SKILL.md`:
a `name` matching its folder, a description of at most 1024 characters that names its
trigger, a body of at most 150 lines, and no name declared twice. It prints one
`FAIL <folder>: <reason>` line per violation and exits 1, or `PASS: 17 skills`. The trigger
rule accepts the forms the native set uses: `when`, `whenever`, `before`, `after`,
`monthly`, `weekly`, `periodic` or `at the end`. `tools/skills/tests/test_lint.py` holds the
fixtures and `tools/factory-tests` runs it.

## Maintenance and evidence

The sibling lifecycle `AUTOMATION.md` is a model-independent maintenance brief. Its run
updates the four source copies first, then rebuilds the passive catalog and verifies
pins, all copied-file/license fingerprints and physical contents. It does not create a timer.
Native Factory edits still require the owner's plan approval; source updates alone
do not authorize policy changes. Existing approvals for the same scope are reused.

The current update strengthens diagnosis, behavioral tests, refusal paths, review
noise filtering, working-state preservation and completion claims. It does not
prove that every LLM will select or follow the right skill. Syntax/link tests and
catalog checks are structural evidence; cross-host task-quality improvement needs
real comparative runs. No hook/runtime installation or new service is required.

A refresh verifies the existing physical pool, materializes a new snapshot, then rechecks
the moved previous snapshot before installing. Previous trees remain in ignored
`.aeion/skill-pool-backup-*` storage; unknown files or local content edits cause a refusal.
The test suite includes concurrent-edit and post-rename interruption regressions.

The three reviewed ECC SAST false positives use per-rule inline annotations, not a pool
exclusion: a fixed verifier argv call and two generated-XML self-checks. The registry
binds each comment to an exact original file hash and line. Catalog entries retain both
original and materialized hashes; a changed upstream file requires renewed review.
