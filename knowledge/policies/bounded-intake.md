---
type: Policy
title: "Bounded tool intake"
description: "Refuse obvious large dumps before execution; use targeted reads and summary commands."
status: stable
generated:
  by: aeion-factory/1.6.2
  at: 2026-10-29
sources:
  - resource: ../../.claude/hooks/guard-path.py
  - resource: ../../.claude/hooks/guard-bash.py
  - resource: ../../.claude/hooks/session-start.py
  - resource: ../../tools/agents/hook.py
  - resource: ../../.claude/hooks/token-feedback.py
  - resource: https://developers.openai.com/api/docs/guides/reasoning-best-practices
    title: "Simple, direct instructions for reasoning models"
  - resource: https://learn.chatgpt.com/docs/agent-configuration/agents-md
    title: "Project instruction discovery and session loading"
  - resource: https://code.claude.com/docs/en/output-styles
    title: "Response style is instruction, not enforcement"
---

# Bounded tool intake

## Intent

Keep useful evidence in context. Prefer `head`, `tail`, `rg -n`, `wc` and `sed -n` with explicit
ranges. For counting/filtering/analysis, print the answer from a small command or script.
Extract errors and summaries from logs, builds and tests; avoid full dumps by default.

## Inputs and defaults

Shared PreToolUse guards inspect native Read/Grep arguments and recognizable Bash dumps.
Constants in the two guards set **64 KiB / 400 lines** for ordinary full-file intake.
Read windows use a positive `limit` and an `offset` of 0 or more (0 and 1 both mean the first
line), at most 400 lines and 64 KiB, with at most 1 MiB of local scanning. Use a bounded shell selection when a distant window exceeds that scan budget.
Large-file Grep uses an explicit positive `head_limit`/native `limit` of at most 400, or an
explicit count/file-name output mode. Directory searches are not recursively pre-counted, but an
explicit unlimited (`head_limit: 0`) content search is refused on any path.

## Outputs and refusals

An oversized full read/dump exits 2 with a short alternative. Edit/Write/patch operations retain
their existing secret guards; editing a large file is not a full read. Known large `cat`, `less`
and `more` calls, dynamic/glob dumps and `find -exec cat` are refused without a bounded terminal
pipeline. Use `head -n 80`, `head -c 65536`, `tail -n 80` or a summary such as `wc -l`.
Keep the bounded pipeline separate from unrelated shell commands. Use `cp` for file copies. The
refusal names its cause: the file over the limit, a variable or glob path, or a `cat` of a relative path
after a `cd` (an absolute path is sized whatever the directory).
Tests remain runnable; quiet/fail-fast flags and error summaries are guidance in this version.

Prompt defense (`.claude/hooks/prompt-defense.py`) never refuses either: it reads at most 64 KiB in
total of a tool result the harness forwards, flags hidden characters, role markers, override phrases
and an encoded payload once per session, and stays silent when no result arrives. The dsh, Pi and OpenCode
plugins forward a result under 256 KiB; Claude Code and Codex pass it through, and the scan still
stops at 64 KiB.

Token feedback (`.claude/hooks/token-feedback.py`) never refuses. Keep reasoning private and use
tools directly; do not emit optional progress narration or intermediate JSON notes. After a tool
call the hook adds one line of context, at most once per turn, when the turn holds visible prose
or JSON notes before or between tool calls. It tolerates one status line of at most 100 characters
for harnesses that require it, and excludes the final answer. It also names a
Write that resent 200+ lines of an existing file where Edit would send only the change. Stop records
each turn's narration in `.aeion/context/narration-<session>.json`. It reads Claude Code and Codex
transcript shapes from a bounded tail, never through a symlink; any other shape or error is silence.
A measured session spent 2% of its transcript on narration and 65% on tool inputs and results, so
the rewrite note and the read limits above carry most of the saving.

Use clear output instructions rather than prescribing a private reasoning format. Project
instructions and advisory feedback cannot guarantee silence across harnesses or override higher
priority instructions. Start a new Codex session to load edited `AGENTS.md` instructions. This
policy changes no model, reasoning-effort or provider setting and claims no measured reasoning-token saving.

## Invariants

Secrets remain refused even with a limiter. Native adapters preserve tool kind and range/count
arguments, so bounded reads work and large-file edits remain available. Guard regressions cover
thresholds, long lines, explicit ranges, real native fields and misleading limiter placement.

## Determinism

Local regular-file metadata and bounded reads establish the decision; no model or new package
is involved. Owner tuning changes the checked-in constants and tests, not an ambient override.
Durable facts belong in Knowledge; session noise stays out of AGENTS.md and handovers.

## Acceptance

Run `python3 .claude/hooks/test_hooks.py` and `python3 tools/agents/tests/test_hooks.py`, then the
existing Knowledge, context, architecture and native-plugin checks. Check real workflow friction
before extending the recognized command patterns.

## Out of scope

**Intake bounds are not output virtualization.** No output is rewritten, no MCP/SQLite/router or
dependency is added. Native tools, line lengths, changing files, shell semantics and arbitrary
commands can still produce large results. This is a conservative accidental-dump safeguard, not
an absolute byte/token ceiling or a complete shell parser. Whole-file work that needs larger
inputs should use task-specific analysis/viewers; no silent guard bypass is introduced.
