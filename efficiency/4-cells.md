# Phase 4 — Cells: skills, the procedures you repeat

> *A cell is a molecule that does one job, again and again, without being told twice.*

**In one line:** every procedure the team repeats becomes a short skill with a verification gate,
loaded only when it is needed.

> **Agent:** enter plan mode. List the procedures this repository repeats (deploy, release, review,
> migration, a data fix) and the corrections a human has had to make twice. Those are the skills.

## Why

A skill costs only its name and one-line description until it is used; its body loads on demand.
That makes it the cheapest place for a long procedure — far cheaper than `AGENTS.md`, which is read
on every task. And a written procedure with a gate does not forget the gate at 2 a.m.

## Anatomy of a good skill

Following Addy Osmani's `agent-skills` anatomy (MIT), adapted:

```markdown
---
name: kebab-case-name            # matches the folder
description: What it does, in the third person. Use when <the trigger>.   # <= ~1000 chars
---

# Title

## Overview        — what and why, three lines, a link to the policy that gives the reasons
## When to use     — triggers, and when NOT to use it
## Process         — numbered steps, each with the exact command
## Rationalizations — | Excuse | Rebuttal |  (the shortcuts an agent will be tempted by)
## Red flags       — signs the procedure is going wrong
## Verification    — checklist items that each need evidence
```

- **Short:** aim for under 60 lines; never over 500. Long material moves to a file beside it
  (`references/`, `scripts/`), one level deep.
- **Never copy a rule** into a skill: link the policy. A skill is *how*, a policy is *why*.
- **Dangerous skills are manual:** `disable-model-invocation: true` (deploy, a data migration).
- **Path-scoped instructions** that should load only near some files go in `.claude/rules/<area>.md`
  with a `paths:` glob list, not in a skill.

## The lifecycle set shipped with Æion Factory

| Skill | Use when |
| --- | --- |
| `plan` | starting any non-trivial task: inspect, propose, wait for a yes |
| `spec` | a feature or component changes: write the spec sections first |
| `build` | implementing in thin, tested slices |
| `test` | adding or fixing tests; the test pyramid; never weaken an assertion |
| `sign-off` | ending a task: tests, docs and links, task state, security on sensitive diffs |
| `pr-review` | a pull request is open: fresh reviewer, verified findings, one verdict comment |
| `ship` | merging and releasing: green CI, changelog, the deploy's own guards |
| `okf-update` | a documented fact changed: the right doc, its links, its caps |
| `security-scan` | a sensitive diff, or the weekly outer loop: `claude-security` |
| `tech-watch` | the monthly watch (Phase 3's method) |
| `pr-taste` | the owner commented on a PR: durable preferences into the knowledge base |
| `retro` | after a session or weekly: lessons, new hook rules, new skills (Phase 7) |
| `graph` | before changing or tracing code: exact structural answers from `tools/architecture/ask` |
| `loop-triage` | an outer-loop finding: turn it into an issue an inner loop can pick up |
| `adopt` | applying this guide to an existing repository, phase by phase |

## Creating and testing skills: `skill-creator`

Anthropic's `skill-creator` plugin (`/plugin install skill-creator@claude-plugins-official`):

1. Interviews you for the intent, edge cases and success criteria, then drafts the `SKILL.md`.
2. Writes 2–3 realistic prompts to `evals/evals.json`, runs them **with and without** the skill in
   parallel subagents, grades each run, and aggregates a benchmark you review.
3. Optimizes the `description` against ~20 trigger and near-miss queries, so the skill loads when
   it should and only then.

Rule of thumb: **a correction made twice becomes a skill or a hook** (a hook if a regex can check
it — Phase 5; a skill if it needs judgement).

## Done when

Each repeated procedure has a skill under its cap; dangerous ones are manual-only; each skill has
been run once for real (or evaluated with `skill-creator`) and its verification items checked.

## Pitfalls

- A skill that restates `AGENTS.md`: delete it.
- A vague description ("helps with deploys"): it will load at the wrong time or never.
- Skills without a verification section: the agent will declare success on vibes.
