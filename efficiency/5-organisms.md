# Phase 5 — Organisms: hooks, the reflexes

> *An organism does not decide to pull its hand from the fire. A good repository does not wait for
> review to notice a secret, a broken link or a stale doc.*

**In one line:** fast, silent-on-success hooks that check every edit, refuse dangerous commands,
and sign off a task before the agent stops — written **after** the docs, to enforce rules that
already exist.

> **Agent:** enter plan mode. List existing hooks (`.claude/settings.json`, git hooks, CI). Propose
> only hooks that enforce a rule written in Phases 1–3. Docs first, hooks second: a hook never
> invents a rule.

## Why

Instructions are context; hooks are enforcement (Claude Code docs: to block an action, use a
hook). Feedback within three seconds of a mistake is the cheapest correction there is — it costs a
few lines of context instead of a failed CI run and a second pull request.

## The reflexes

| Reflex | Event | What it does |
| --- | --- | --- |
| **Orientation** | `SessionStart` (startup, resume, compact) | prints at most 25 lines: `git status`, the last commits, the open tasks of `work/current.md`, the health scorecard |
| **Guard** | `PreToolUse` on `Bash` and on `Read/Edit/Write/Grep` | refuses reading secret files, environment dumps, force-pushes and `--no-verify` (exit 2 with the reason) |
| **Check after edit** | `PostToolUse` on `Edit/Write` | runs only the checks that apply to the edited file (knowledge checks and documentation hints; add project lint/size checks explicitly); silent when fine, at most 15 lines when not; names the doc that covers the file, once |
| **Sign-off** | `Stop` | if the branch changed code without its covering docs, the task state or the map, blocks **once** with the list; the same findings never block twice, and a second stop always passes |
| **Pre-commit** | git `pre-commit` (`git config core.hooksPath tools/git-hooks`) | the same checks for every committer, human or agent |
| **Context checkpoint** | session, prompt, tool, compact and stop events | 250k alert and closure-only work; current handover/docs required before compaction; entire-run stop at observed 300k or unavailable usage |

Rules for every hook: under three seconds; exit 0 and silent on success; exit 2 with the rule and
its fix on failure; never a hook that loops (the sign-off uses `stop_hook_active` and a
per-session memory of what it already said); tested (`.claude/hooks/test_hooks.py`).
The context adapter has a five-second hook deadline and separate tests
(`tools/context/tests/test_budget.py`). Its strict pre-request ceiling is unqualified; see
`knowledge/operations/context-safety.md`. Claude, Codex, OpenCode and Pi share one context rule: a 250k closure alert, a verified handover, then compaction at 250k; 300k forces the handover and compaction again.
The adapters share guards/checkpoints, with the exact supported events and limits documented in
`knowledge/operations/agent-compatibility.md`; they do not copy Claude settings blindly.

## Rules from corrections: `hookify`

Anthropic's `hookify` plugin (`/plugin install hookify@claude-plugins-official`) writes simple
hook rules as Markdown files, `.claude/hookify.<name>.local.md`:

```markdown
---
name: warn-console-log
enabled: true
event: file              # bash | file | stop | prompt | all
conditions:
  - field: new_text
    operator: regex_match
    pattern: console\.log\(
action: warn             # or block
---
Remove debug logging before committing; use the project's logger.
```

- `/hookify <instruction>` writes a rule; `/hookify` alone reads the recent conversation and
  proposes rules from the corrections you made. Rules apply on the next tool use, no restart.
- Use it for **checkable taste** (a forbidden pattern, a required header) that the retro of Phase 7
  surfaces; keep logic-heavy checks in real scripts with tests.

## Files this phase creates or merges into

`.claude/settings.json` (hooks), `.claude/hooks/*.py` and their tests, `tools/git-hooks/pre-commit`,
`.claude/hookify.*.local.md` (examples, disabled until wanted), `.claude/rules/*.md` (path-scoped).

## Done when

A deliberate violation of each rule is caught in under three seconds (a secret read refused, a
broken link reported, a code change without its doc signed off once), and the hook tests pass in CI.

## Pitfalls

- A `Stop` hook that blocks every turn: an infinite, expensive loop. Block once per finding set.
- Hooks that print on success: context noise on every edit.
- A hook that silently auto-fixes: the agent learns nothing and the diff surprises the reviewer.
