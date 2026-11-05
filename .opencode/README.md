# OpenCode integration

Read the [setup runbook](../knowledge/operations/agent-compatibility.md).
Root opencode.json enables native auto-compaction and points at the maintained Claude skill
source. The local V2 plugin reuses existing Python guards, edit checks and handover checkpoints.
OpenCode also discovers the shared .agents/skills links; bodies are maintained once.

Launch with `tools/agents/run opencode`. The plugin uses Node built-ins and declares no SDK dependency.

If your existing OpenCode database is incompatible, `tools/agents/run opencode --isolated`
selects project-local XDG data/config/state/cache under ignored .aeion/opencode. Connect your
provider through OpenCode's own UI for that separate profile; never copy stored credential files.
The existing user database and configuration remain yours.

OpenCode 2.1.4+ uses a default id/setup plugin entrypoint and native domain callbacks. It refuses compaction without the verified
handover and injects its recovery pointer. Use the shared sign-off skill at task completion. The plugin feeds each step's tokens to the shared 250k/300k rule and compacts itself; no invented fixed 250k
setting or strict/observed 300k runtime cap is advertised.

## Live note: 250k compaction (2026-11-02)

A live `opencode run` (2.2.0, `deepseek-v4.1-flash`) compacted a 272k-token step on a turn with two
tool calls (state `RECOVERING`, epoch 1). A turn with only one tool call can miss the trigger: the
plugin measures `session.step.ended`, which arrives after `tool.execute.after`, so the next tool call
or turn sees the count. If the turn stops after one tool, keep the session going or verify the
checkpoint and start a new session from the handover.
