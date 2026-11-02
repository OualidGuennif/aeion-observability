# Pi integration

Read the [setup runbook](../knowledge/operations/agent-compatibility.md).
Pi 1.4.0+ reads the root `AGENTS.md`/`CLAUDE.md` and the shared `.agents/skills` links from any folder
below the root; bodies are maintained once. The project extension in `extensions/factory/` reuses the
existing Python guards, edit checks and handover checkpoints through `tools/agents/hook.py pi`.

Launch with `tools/agents/run pi` and trust the project when Pi asks, so `.pi/extensions/` loads. Pi loads
project extensions from its start folder only: started elsewhere, pass it explicitly
(`pi -e ../.pi/extensions/factory/index.js` from `demo/`). The extension uses Node built-ins only.

It blocks a tool call on any refusal or hook failure, appends edit feedback to the tool result, gives
the factory context once per session and again after a compaction, and cancels a compaction without the
verified handover. The 250k alert names the checkpoint command, and closure admits a project's own
Markdown docs. Use the shared sign-off skill at task completion. Pi controls its own compaction
window (`compaction.reserveTokens`). At 250k, once the handover is verified, the extension compacts at
the settlement boundary in an interactive or RPC run and resumes from the handover. A one-shot
print/JSON run cannot finish that async summary, so it stops cleanly with the verified handover and a
notice instead of crashing (see below). At 300k only the handover and its checkpoint remain, and Pi
compacts there whether or not the checkpoint verifies. A settlement that still owes closure is continued at most
three times, then settles with the reason in the UI; any other terminal stop (`continue: false`) settles
at once with its reason shown, never as another request.

## Headless 250k: clean stop (1.9.2)

A live `pi -p` run (1.4.0) at 264,275 measured tokens hits the 250k gate and exits 0 when the handover
and checkpoint verify. The extension no longer calls `ctx.compact()` from `tool_result` or from a
one-shot settlement: Pi's manual compaction aborts the running turn, and print mode disposes before the
summary is written. The run prints a notice on stderr, writes no compaction entry, and leaves the
state at `HANDOVER_REQUIRED`; start a new session from `work/handovers/` to continue. Interactive (TUI)
and RPC runs compact at settlement and resume with the start context; both are implemented but not
live-tested.
The 1.9.1 failure (stale-ctx `onError`, exit 1) is fixed.
