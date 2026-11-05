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
the settlement boundary and resumes from the handover. At 300k only the handover and its checkpoint
remain, and Pi compacts there whether or not the checkpoint verifies. A settlement that still owes
closure is continued at most three times, then settles with the reason in the UI; any other terminal
stop (`continue: false`) settles at once with its reason shown, never as another request.

## Headless runs

One-shot `pi -p` (and `--mode json`) disposes the process at settlement, so an asynchronous compaction
started there is lost. The extension therefore never starts one in those modes: a `pi -p` run at 250k
with the verified handover and checkpoint exits 0, prints a notice on stderr, writes no compaction
entry, and leaves the state at `HANDOVER_REQUIRED`. Start the next session from `work/handovers/` to
continue. This is the 1.9.2 clean stop; the 1.9.1 crash (stale-ctx `onError`, exit 1) is fixed.

For a headless run that compacts and resumes in one process, use the factory RPC runner:

```bash
tools/agents/run pi rpc --provider opencode-go --model deepseek-v4.1-flash -- "the task"
tools/agents/run pi rpc --prompt-file task.md
```

It starts `pi --mode rpc` with this extension, sends exactly one prompt, streams the assistant text,
waits through `compaction_start`/`compaction_end`, the extension's resume run and the final
`agent_settled`, and exits only after a settled quiet period. Pi starts the settlement compaction only
after it emits `agent_settled`, so an aborted settlement waits `--compaction-wait` seconds for that
compaction instead of the normal grace. Client options: `--prompt-file PATH`, `--timeout SECONDS`
(default 1800), `--grace SECONDS` (quiet time after a normal settlement, default 2),
`--compaction-wait SECONDS` (default 10), `--pi-executable PATH`; Pi options go before `--`, and the
prompt after it. The runner owns `--mode rpc` (a conflicting or repeated one is refused) and the
extension path. Exit codes: 0 settled, 1 refused prompt, early exit, no settlement or a failed
compaction, 2 usage error.

The fake-RPC tests (`tools/agents/tests/test_pi_rpc.py`, part of `tools/factory-tests`) prove the
framing, the compaction wait and the resume without model calls. A live 288,668-token run on
2026-11-02 then reached the gate, verified its handover, and the extension's settlement compaction
wrote a compaction entry and resumed the task in the same process. That run was stopped while the
resumed work was in progress, so it did not observe the runner's own exit; the fake compaction test
and a real short RPC call cover the exit. The qualification section of
[compatibility](../knowledge/operations/agent-compatibility.md) records it.
