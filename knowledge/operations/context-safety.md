---
type: Runbook
title: "Context safety and handover"
description: "One 250k/300k rule for Claude, Codex, OpenCode, Pi and dsh: closure, verified handover, compaction, and its limits."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.1
  at: 2026-10-25
sources:
  - id: budget
    resource: ../../tools/context/budget.py
    title: "Budget state and documentation checkpoint"
  - id: hook
    resource: ../../.claude/hooks/context-budget.py
    title: "Claude hook adapter"
  - id: settings
    resource: ../../.claude/settings.json
    title: "Default registrations and compaction window"
  - id: tests
    resource: ../../tools/context/tests/test_budget.py
    title: "Boundary and failure regressions"
  - id: adapters
    resource: ../../tools/agents/hook.py
    title: "Codex, OpenCode and Pi usage readers"
  - id: launcher
    resource: ../../tools/context/run
    title: "Managed launch and unsupported strict refusal"
---

# Context safety

[Bounded intake](../policies/bounded-intake.md) reduces obvious large Read/Grep/Bash dumps before
execution. Intake bounds are not output virtualization: no tool result is rewritten, and these
heuristics cannot establish an absolute context ceiling. Keep targeted reads and summary commands.

The default Claude profile enables native auto-compaction at 250,000 tokens and a budget hook
on session start, prompts, tools, compaction and stop. SubagentStop also checks a child's final
observation, including pure-text child responses. The hook reads only the current session's
bounded transcript tail and retains native token counts, never transcript text. Cached input
counts once. Synthetic assistant records (API errors and hook stops, model `<synthetic>`) were
never sent and are skipped, so a stop cannot hide the last real request and block every later
prompt. After a "prompt is too long" error the real context may exceed that last observation; the
request itself still fails natively. Missing or zero usage is unavailable, not an empty context. An incomplete final JSONL line is
a transient write; a malformed complete record is invalid.

Every event latches the first observed 250k crossing, including PreCompact. The hook alerts both
agent and user at the next supported event; PreCompact retains a pending alert because that event
discards system messages. Only closure work
(docs/task/handover edits and fixed verification commands) remains available. At an observed
300k closure narrows to the handover and its checkpoint (reads stay open), Stop is refused, and the
message asks for the handover and compaction now. 300k never stops the run: once the checkpoint is
verified, compaction runs again and the session continues from its handover. A failing check does not
recreate that stop at 300k: code is frozen there, so a check that failed before the session could be
neither verified nor repaired. At 300k the hook signals the adapters to compact whether or not the
checkpoint verifies, lets that compaction through, records that the closure is still owed
(`closure_owed`), and admits code edits in the new epoch with a warning that names the checkpoint
command; Stop stays refused until a verified receipt settles the debt on the next event that reads the
receipt. Codex and Droid keep their own early-compaction path, which still resumes in closure. Below
300k the refusal is unchanged, so a session that must repair code compacts at 300k. The checkpoint
itself is not weakened: it still runs every check over the whole tree and refuses on any failure. The
session state and active handover survive restart. Each session has its own file lock and atomic state.
Tool events carrying `agent_id` use a separate parent/agent key and that child's transcript,
including the documented nested `subagents/agent-<id>.jsonl` layout and a workflow's
`subagents/workflows/<run>/agent-<id>.jsonl`. Missing child usage refuses
the child; it never reads the parent's counters or changes the parent's stop state. Child
handover/checkpoint commands use the separate key printed by the guard.

Before any compaction, fill `work/handovers/<session-id>.md`, update `work/current.md` and affected
docs, and run `python3 tools/context/budget.py checkpoint --session <id> --base <git-ref> --verify`
(`--base` only under git; a plain folder skips the diff and task-state checks).
The command runs knowledge/link/health checks and binds readiness to the current source diff
and handover hash. Later edits invalidate it. A refused check names the check and a bounded tail of
its output, so the agent can fix the failure instead of retrying a bare exit status. Compaction is
refused without a current receipt, and the refusal names the paths changed since it: a live session
log inside the tree changes on every event, so it is git-ignored (`/demo/*/journal/*.jsonl`) or
written outside the project.
Local mode (`git config aeion.mode local`, read with `--local` so includes and the global config
do not count) keeps no `work/current.md` entry, so its checkpoint
does not require one. During closure a command the shell cannot parse is denied, never a stop.
Closure admits edits to any Markdown file in the project, so a project's own docs can be updated,
and never a code file. The checkpoint is admitted from any working directory when its path resolves
to this root's `budget.py` (relative to the shell's folder, absolute, or after a `cd <root> &&`
prefix), and a bare `cd <root>` is admitted; any other `cd`, chain or session is denied. The
handover has the exact lines `## Scope`, `## Completed`, `## Remaining`, `## Constraints` and
`## Evidence`; the 250k and 300k messages name the checkpoint command and those lines, and a
refused checkpoint names each missing heading and any remaining TODO.
The skeleton appears only when closure needs it (the 250k alert, the 300k forced closure, a refused
compaction or the first checkpoint command), so ordinary sessions and subagents leave none; replace each TODO. Keep outcomes, remaining
work, constraints and evidence concise. These local handovers are ignored by Git; durable facts
belong in Knowledge. After compaction the same file is the recovery pointer.

Startup and the first prompt allow a native bootstrap before usage exists. All later work
requires a positive native observation. A bounded retry waits for asynchronous transcript writes;
unavailable usage denies the current tool call (the agent keeps running and may retry it;
PostToolUse passes; other events stop) without latching STOPPED, so a later valid observation
can recover. A PostToolUse warning from the prompt-defense scan travels in the same assistant
context and changes no budget decision. Invalid complete records remain terminal: that is an
integrity failure, not a size. A `compact_boundary` or compact SessionStart clears the
old observation and ends a 250k or 300k closure. Smaller model windows retain
their native earlier limit. The guard does not expand a model's capacity.

**Guarantee:** this is checkpoint-based enforcement, not a proof of an absolute 300k ceiling.
Claude Code exposes no qualified before-every-request admission callback here. A large tool
result or response may cross a threshold before another hook runs. `tools/context/run --strict`
therefore refuses execution rather than advertising unsupported strict protection. Codex, OpenCode and Pi apply the same rule through `tools/agents/hook.py`, from the context size
each harness measures; see [compatibility](agent-compatibility.md). A Pi settlement that still owes
closure is continued three times, then settles with the reason shown instead of repeating one alert.
A live Claude 250k/300k long-session run remains unverified.

The [2026-10-26 OpenCode experiment](../references/opencode-context-qualification.md) exercised a
real paid DeepSeek V4.1 Flash call with 278,859 input tokens and a native refusal after a tool result
crossed the experimental reserved budget. It establishes a primary HTTP admission mechanism in
an isolated profile; it does not enable Æion Factory strict mode or qualify handover/compaction and
auxiliary-call coverage.

Use `tools/context/run [claude arguments]` for managed interactive/headless runs. It checks the
current architecture baseline (a warning, not a refusal, when absent), passes `--autocompact 250000`,
and refuses explicit compaction overrides. Hooks are an accidental-behavior guard, not isolation against malicious code that can
edit its own scripts/settings. Raw CLI launches outside the managed entry point are not qualified.

## One rule, five harnesses

| Harness | Context size it measures | Compaction at 250k |
| --- | --- | --- |
| Claude Code | the session transcript's last request | native, `autoCompactWindow: 250000` |
| Codex | the rollout's newest `token_count` after the newest `compacted` record | native at 250000 (`model_auto_compact_token_limit`); a compaction before the handover owes it after |
| OpenCode | the newest `session.step.ended` tokens (input, output, cache) | the plugin calls `session.compact` |
| Pi | `ctx.getContextUsage().tokens` | the extension calls `ctx.compact()` |
| dsh | `ctx.tokenMeter.measure(session).totalTokens` | the plugin compacts before the next step |
| Droid | nothing (no 250k alert) | native; a compaction before the handover owes it after, as for Codex |

A harness reports usage after the response that asked for a tool, so the adapter keeps the last count
until a new one arrives (0 after a compaction). A malformed count or a rollout from another session
fails closed. Codex without a `transcript_path` keeps only its native compaction and refusal. Pi and
OpenCode compact themselves on the hook's `aeion.compact` signal, sent once a closure's checkpoint
is verified, so the context never waits for the model window. OpenCode sends no compact SessionStart, so
its allowed compaction itself ends the closure (state RECOVERING, usage cleared). Codex ends its turn on a
refused compaction and retries it before every turn, so it would stall: when Codex compacts before its
handover is verified (owner decision 2026-10-28), the compaction runs and the session resumes in closure,
allowed only the handover, `work/current.md`, docs and the checkpoint until the checkpoint passes. The OpenCode stream and compaction
calls are read from the 2.2.0 build and unit-tested; a live long run has not exercised them yet.

Verification: `python3 tools/context/tests/test_budget.py`, `tools/agents/tests/test_hooks.py`,
`test_pi.mjs` and `test_opencode.mjs`. Synthetic fixtures prove state and
refusal behavior; they do not establish live runtime guarantees. The existing Stop hook remains
a once-only normal sign-off reminder, separate from the mandatory pre-compaction checkpoint.

All three managed entry points are available through `tools/agents/run <agent>`. The original
Claude entry point remains supported and now always enters the repository root before launch.

Checkpoint task-state checks include nonignored untracked files, not only tracked diffs. A resumed
pending warning asks for closure; only a verified actual compaction can report a retained checkpoint.
