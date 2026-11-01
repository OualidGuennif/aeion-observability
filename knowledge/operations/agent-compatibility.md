---
type: Runbook
title: "Claude Code, Codex, OpenCode, Pi, dsh, Devin, Droid and Antigravity"
description: "One Æion Factory instruction/skill source, runtime-specific adapters, setup and explicitly bounded guarantees."
status: stable
review_after: 2027-01-29
sources:
  - resource: ../../tools/agents/hook.py
    title: "Native payload adapter"
  - resource: ../../tools/agents/run
    title: "Managed agent launch"
  - resource: ../../tools/agents/adapter-check
    title: "Connector copy drift check"
  - resource: ../../.codex/config.toml
    title: "Codex native compaction config"
  - resource: ../../.codex/hooks.json
    title: "Codex hook registrations"
  - resource: ../../opencode.json
    title: "OpenCode native config"
  - resource: ../../.opencode/plugins/factory/index.js
    title: "OpenCode plugin callbacks"
  - resource: ../../.pi/extensions/factory/index.js
    title: "Pi extension events"
  - resource: ../../.dsh/factory.patch.yml
    title: "dsh patch overlay"
  - resource: ../../.dsh/plugins/factory/index.js
    title: "dsh plugin guard and compaction"
  - resource: ../../.devin/config.json
    title: "Devin import settings"
  - resource: ../../.devin/hooks.v1.json
    title: "Devin hook registrations"
  - resource: ../../.factory/settings.json
    title: "Droid hook registrations"
  - resource: ../../.agents/hooks.json
    title: "Antigravity hook registrations"
  - resource: ../../.dsh/plugins/factory/compaction.js
    title: "compaction.js, which names this doc as its spec"
  - resource: ../../.dsh/plugins/factory/seam.js
    title: "seam.js, which names this doc as its spec"
generated:
  by: aeion-factory/1.6
  at: 2026-10-29
---

# Agent compatibility

AGENTS.md, Knowledge, task state, checker commands and the reviewed PR workflow are shared.
Claude Code remains the original integration. Codex, OpenCode, Pi, dsh, Devin, Droid and Antigravity use their
documented native configuration and small adapters to the existing guards/checkpoints; copying a
directory does not establish loaded hooks or identical runtime guarantees.

## Contract

- Keep existing `.claude/skills` as the maintained skill source. Codex discovers symlinked folders
  under `.agents/skills`; OpenCode already discovers the Claude-compatible paths.
- Codex local trusted projects enable `.codex/config.toml` and `.codex/hooks.json`. Its native
  auto-compaction threshold is 250000. Codex has no compaction tool and ends its turn on a refused
  compaction, so a compaction that comes before the verified handover runs, and closure is owed right
  after it. Its rollout is not a stable token API.
- OpenCode 2.1.4+ loads root `opencode.json` and `.opencode/plugins/factory/index.js`. The plugin reads each
  step's tokens (`session.step.ended`) and compacts itself at 250k once the handover is verified.
- Pi 1.4.0+ reads `AGENTS.md`/`CLAUDE.md` from its folder and every parent, and project
  `.agents/skills` from its folder or a parent, so the shared rules and skills need no copy. It loads
  `.pi/extensions/factory/index.js` from **its start folder only**, once the project is trusted; started
  elsewhere (`demo/`), pass it explicitly: `pi -e ../.pi/extensions/factory/index.js`. The extension sends
  `before_agent_start` (once per session, and again after a compaction) as SessionStart, `tool_call` as
  PreToolUse (`{block: true, reason}`, also on any hook failure), `tool_result` as PostToolUse (feedback
  appended, `structuredContent` kept) and `session_before_compact` as PreCompact (`{cancel: true}` and a
  notification without a verified handover) to `tools/agents/hook.py pi`. `bash` and `powershell` are
  Bash, `read`/`edit`/`write`/`grep` name their file in `path`, `find` and `ls` are Glob and LS, and an
  unknown tool carrying a `command` string is a shell call. `tools/agents/run pi` requires 1.4.0+.
  Its compaction aborts the running turn, so once it is done the extension sends a message that resumes
  the task from the handover.
  The extension sends `ctx.getContextUsage()` to the shared rule and calls `ctx.compact()` at 250k once
  the handover is verified; the 250k alert names the checkpoint command, and closure admits a project's
  Markdown docs. `agent_before_settle` sends Stop: a sign-off finding becomes a displayed
  `custom_message` entry with `continue: true` (one more request); the hook shows each finding once, so
  the next settlement passes. A terminal stop (`continue: false`: a stopped run, invalid or unavailable
  usage) settles at once and shows its reason in the UI, never as another request. A closure refusal
  repeats at most three times and then settles with the
  reason in the UI, so one alert cannot spin forever. Not yet qualified live: the events follow the
  1.4.0 docs and published type declarations.
- Token feedback (narration between tools, full-file rewrites; advisory, never blocking) covers
  Claude Code natively and Codex through its rollout transcript. Devin, Droid and Antigravity pass
  no transcript the hook can read and the OpenCode and Pi extensions pass no assistant text, so they get the
  written rule in `AGENTS.md` only; the adapter stays silent for them and keeps working.
- In a plain folder without git, every hook command falls back from `git rev-parse --show-toplevel`
  to the current folder, so the adapters run where the agent starts. Limit: a plain folder started
  from a subfolder, or nested in another repository, does not find `tools/agents/hook.py`; Codex and
  Antigravity then refuse every tool call (fail closed). Start the agent at the project root.
  Inside a git repository a subfolder such as `demo/` works: the hook commands resolve the git root,
  and the OpenCode and Pi extensions use the nearest folder above their start folder that has
  `tools/agents/hook.py`.
- Both adapters enforce supported Bash/path refusals, edit feedback and a verified handover
  before compaction; the first refused compaction creates the skeleton to fill. Native token stops and strict pre-request 300k admission are unqualified.
- dsh (DeepSeek Harness, CLI `dsh`, 0.2.1-rc.3) reads `AGENTS.md`/`CLAUDE.md` from the project root down
  to its folder and skills from `.dsh/skills` and `.agents/skills`, so the shared rules and skills need no
  copy. It loads project plugins only from a patch overlay: `tools/agents/run dsh [web|headless]` (web, a
  browser UI, by default; dsh ships no `tui` profile) passes `--patch .dsh/factory.patch.yml`, which
  inserts `.dsh/plugins/factory/index.js` (the guards) and `compaction.js` (the compaction service, shared
  through `seam.js`). The web profile keeps `compaction` inside each agent preset, not at its root, so there
  the second entry stays pending ("waiting for service: compaction") while the guards run. One web server
  serves many projects, so the plugin finds `tools/agents/hook.py` above each session's own directory
  (`ctx.workingDirectory.get(session)`, which follows the working-directory tool), not the launch folder;
  a session outside an Æion Factory project is left alone. The plugin's
  `ctx.tools.guard` sends every tool call as PreToolUse to `tools/agents/hook.py dsh` (a returned reason
  denies it and no later policy can undo that; a call without an agent is refused), with
  `ctx.tokenMeter.measure(session).totalTokens` as the usage; `tools/post-execute` sends PostToolUse.
  dsh has no hook that adds text to the prompt, so the SessionStart context (the checkpoint profile and
  recovery pointer) is steered to the agent on its first guarded call; `agent/turn-stopping` sends Stop,
  and a sign-off finding is steered as one more step (shown once per session, so it cannot loop). An
  answer of `continue: false` is the hook's terminal stop: the turn ends with its reason and is never
  steered, because a steered terminal stop starts a turn that closes the same way.
  Once a verified handover asks for compaction, the next `agent/pre-step` sends PreCompact and, when
  allowed, compacts through `ctx.compaction.compactIfNeeded(agent, 'context-overflow')`, then steers a
  message that resumes from the handover. Without the root service (web) it steers the agent to ask the
  user for `/compact`; a token measure that falls to under half between two calls marks that compaction,
  so the next call sends SessionStart with `source: compact`. `bash` is Bash, `read`/`write`/`edit` name `file_path`,
  `str_replace_editor` is Edit (Read for `view`), `glob`/`grep` are Glob/Grep. dsh's own pressure
  compaction (about 55% of a 1M window) is not refused; past 300k only closure runs, so it is reached
  only if closure never completes. A dsh launched without the patch has no Æion Factory hooks.
  Its sandbox ("workspace-write") writes only below the launch folder and headless has no approval
  channel: launched in a subfolder (`demo/`), it cannot write the root's `.git`, `work/current.md` or
  `work/handovers/`, so whoever drives the run commits and writes the closure files there; launched at
  the root, closure works. Programs that keep state in the home folder need it moved inside the
  workspace, e.g. `DOCKER_CONFIG=$PWD/.docker` (with the CLI plugins linked) for `docker compose`.
- Devin CLI reads `AGENTS.md` and `.agents/skills` natively. By default it also imports
  `.claude/settings.json` hooks, but its tools are named `exec`, `read`, `edit`, `write` and
  `apply_patch`, so Claude matchers never fire and the matcher-less Claude budget hook reads a
  transcript Devin does not write. `.devin/config.json` therefore turns the Claude import off, and
  `.devin/hooks.v1.json` sends SessionStart, PreToolUse, PostToolUse and Stop (no matchers) to
  `tools/agents/hook.py devin`. The adapter maps the tool names (also `bash`, `shell`, `grep`, in
  any case) to the shared guards; an unknown tool carrying a `command` string goes through the
  shell guard, and through the path guard too if it names a file. A refused tool call gets
  Devin's `{"decision": "block", "reason": ...}`; a failed Stop or SessionStart gets
  `continue: false`, because Devin's block on Stop means "keep going".
  A payload without `session_id` uses one key per clone, so sign-off reminders are shared across
  that clone's Devin sessions. Each registration also passes its event name (`hook.py devin
  PreToolUse`), used when a payload names none, so such a payload is judged as that event instead
  of stopping the session. Devin has no Æion Factory compaction checkpoint or token stop.
- Droid, the CLI of Factory (factory.ai, a product separate from Æion Factory), reads `AGENTS.md`,
  `.agents/skills` and `.factory/settings.json`. That is why Æion Factory's local state lives in
  `.aeion/` and only Droid's config is tracked in `.factory/`. Its hooks send SessionStart,
  PreToolUse, PostToolUse and Stop to `tools/agents/hook.py droid`. Droid payloads and decisions
  are Claude-shaped; the adapter maps `Execute`, `Create` and `ApplyPatch` (patch text in
  `command`, `patchText`, `patch` or `input`) to the shared guards; a tool outside the known
  names carrying a `command` string goes through the shell guard (and the path guard for a
  file). It refuses with `permissionDecision: deny`. As for Devin, each registration passes its
  event name and a payload without `session_id` uses one key per clone, so a missing field refuses
  nothing by itself. Droid passes no token count, so it gets no 250k alert or 300k stop, but its
  PreCompact (documented with `trigger` manual or auto) reaches the adapter: a compaction before a
  verified handover runs, since Droid documents no way to refuse one, and its compact SessionStart
  then allows only closure (handover, `work/current.md`, docs, checkpoint) until the checkpoint passes.
- Google Antigravity (the `agy` CLI and the IDE) reads `AGENTS.md` and `.agents/skills`, and
  workspace hooks from `.agents/hooks.json` once the folder is trusted. One `aeion-factory` group
  sends PreToolUse and PostToolUse (matcher `.*`) and Stop to `tools/agents/hook.py antigravity
  <event>`: the payload names no hook event or session, so the event is an argument and the
  session key is per clone, as for Devin. The adapter reads `toolCall {name, args}`, maps
  `run_command` (`CommandLine`) to Bash, `view_file` to Read, `write_to_file` to Write and
  `replace_file_content`/`multi_replace_file_content` to Edit and `grep_search` to Grep. For any
  tool, including MCP tools, every nonempty string at any depth under an argument whose name,
  ignoring case and `_`/`-`, ends in path, file, dir, directory or uri, or their plurals
  (`AbsolutePath`, `TargetDirectories`, `file_path`, `Uri`; a `file:` URI is decoded to its path),
  goes through the path guard; `view_code_item`'s `NodePaths` are code symbols and are skipped. A
  mapped file tool with none is refused. Not recognized: other names (`target`, `Url`), text typed
  into a running command (`send_command_input`) and Windows paths. `view_file`'s
  `StartLine`/`EndLine` become the intake window; `grep_search` with `MatchPerLine: false` lists
  names only. For any tool, every string at any depth under an argument whose name ends in
  include, glob or pattern, or their plurals (`Includes`, `IncludePattern`, `file_pattern`), goes
  through the same check as Claude's Grep `glob` filter ([security](../policies/security.md)),
  with its limits; a non-string filter is refused. Any tool with a `CommandLine` goes through the
  shell guard, as does a `command` or `commandLine` argument in any case; a call with two is
  refused. `Cwd` or `workdir` in any case (a `file:` URI decoded) is the shell's directory; two
  or a non-string one are refused. On a shell call any other argument must be a flag or a
  number, since the guard cannot tell which one a tool runs in; a text, list or object is refused.
  The guards see only fields the adapter derives, never a raw `limit` or output mode from the
  model. A pre-tool payload without `toolCall` is refused. A pre-tool answer is always an
  explicit `{"decision": "allow"}` or `{"decision": "deny", "reason": ...}`, since Antigravity
  reads an empty answer as a refusal. Unverified until a live run: whether that `allow` also
  skips Antigravity's own approval prompt (a `run_command` with `SafeToAutoRun: false`); until
  then, assume it may. No compaction checkpoint or token stop.
- Managed CLI launchers enter the repository root and check the exact-HEAD architecture baseline;
  its absence is a warning, because installing the integrations needs the user's yes.
- Raw command/MCP paths, host-managed/cloud orchestration and deliberate local modification are
  outside any complete isolation claim. Native project/hook trust and sandbox controls still apply.
- The shared launcher also aligns `PWD`: OpenCode 2.1.4 uses it to select the run's location, so
  changing only the process working directory can load another project's plugin/configuration.

## Verification

Test real tool payloads, patch paths, denied secrets, checker failures and compaction with and
without a current checkpoint. A missing callback/runtime is unverified, never a pass. Runtime
qualification and setup commands are recorded below.

## Primary interfaces

- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/build-skills
- https://opencode.ai/v2/docs/build/plugins/
- https://opencode.ai/v2/docs/config/
- https://opencode.ai/v2/docs/skills/
- https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs (extensions, skills,
  configuration, security; event types in `src/core/extensions/types.ts`)
- https://docs.devin.ai/cli/extensibility/hooks/overview
- https://docs.devin.ai/cli/reference/configuration/read-config-from
- https://docs.devin.ai/cli/extensibility/skills/overview
- https://docs.factory.ai/reference/hooks-reference
- https://docs.factory.ai/cli/configuration/hooks-guide
- https://docs.factory.ai/cli/configuration/skills
- https://antigravity.google/docs/hooks
- https://antigravity.google/docs/rules
- https://github.com/google-antigravity/antigravity-cli/blob/main/CHANGELOG.md

## Setup

1. Follow the [getting-started checks](getting-started.md). Offer the recommended architecture
   baseline and install it only on the user's yes ([architecture maintenance](architecture-maintenance.md)). Install the
   chosen native CLI separately; preserve user account/provider settings.
2. Claude: trust the workspace, then `tools/agents/run claude`.
3. Codex: trust the project in native settings, review/enable the local hooks in `/hooks`, restart,
   then `tools/agents/run codex`. A trusted project and trusted hook sources are distinct. Do not
   disable trust checks globally to make discovery appear successful.
4. OpenCode: `tools/agents/run opencode`. The root config selects the maintained skill directory;
   the native loader loads the local plugin directory. A database schema conflict can use
   `--isolated`, a separate ignored XDG profile; connect that profile's provider natively.
5. Pi: `tools/agents/run pi` (1.4.0+). Trust the project when Pi asks, so `.pi/extensions/` loads;
   the startup list names `factory`. Connect the provider in Pi's own settings.
6. Devin CLI: `devin` or `tools/agents/run devin` from the repository root. Approve the project
   hooks if Devin asks. Keep the model/provider choice in Devin's own user settings.
7. Droid: `droid` or `tools/agents/run droid` from the repository root. Approve the project hooks
   if Droid asks; account and model stay in Droid's user settings (`~/.factory/`).
8. Antigravity: `agy` or `tools/agents/run antigravity` from the repository root, or open the
   folder in the IDE. Trust the folder so `.agents/hooks.json` loads; `/hooks` lists it.

The shared guards are basename/command-pattern safeguards. Codex native Bash and apply_patch
payloads are normalized explicitly, including deleted/moved patch paths. OpenCode maps native
camelcase file paths and tool events, appends edit feedback to tool output, and injects the exact
verified handover pointer during compaction. Use the shared sign-off skill before finishing;
the plugin does not claim an idle hook forces continuation. Shell edits and arbitrary MCP tools are not complete edit coverage.

The adapter preserves Read/Grep range/result limits and the real edit kind when invoking shared
[intake guards](../policies/bounded-intake.md). OpenCode V2 uses `path`, 1-based `offset` and
`limit`; Grep's native `limit` is accepted alongside Claude's `head_limit`. Patch path checks use
Edit semantics, so checking a patch never becomes an accidental full-file Read refusal.

## Keeping a copy in step

A project that adopts the factory carries its own copy of every connector: the shared adapter
(`tools/agents/hook.py`), the context rule (`tools/context/budget.py`), the Claude hooks, the dsh
plugin, the Pi extension, the OpenCode plugin and the native registrations. A copy that drifts from
the factory does not fail loudly. The harness keeps loading whatever is there, or silently drops a
module that no longer parses, and nothing in the session says so: that is how a desktop dsh profile
ran for hours with no factory hooks at all while the factory's own copy was green.

`tools/agents/adapter-check` compares a repository's copies with the factory copy the script ships
in, by exact bytes:

```bash
tools/agents/adapter-check                  # this repository
tools/agents/adapter-check --root ../app    # a project that adopted the factory
tools/agents/adapter-check --root ../app --strict --verbose
```

It prints one line per connector: `ok`, `DRIFT` with both sizes and the exact `cp` that repairs it,
`UNWIRED` for a native config that names a file which is not there, and `invalid` for a config that
is not valid JSON. A connector the project does not carry is `absent`: listed under `--verbose`, and
a failure only under `--strict`, because a Claude-only project legitimately has no Pi extension.
Exit code 0 is clean, 1 is drift or broken wiring, 2 is a bad root or the script's own copy.

Configs a project merges with its own settings are not compared byte for byte —
`.claude/settings.json`, `.codex/config.toml`, `.devin/config.json` — but their commands are: every
script they name must exist. Run the check after adopting, after every factory upgrade, and in the
project's own CI — from a pinned factory checkout with `--root`, never from the copy inside the
project, which would compare the project with itself and pass; the factory's own run passes
`--self`. The factory runs it on itself in `tools/factory-tests`, which catches a
registration that points at a renamed or deleted module.

## Qualification and limits

Regression commands: `python3 tools/agents/tests/test_hooks.py`,
`python3 tools/agents/tests/test_adapter_check.py`, `tools/agents/adapter-check`,
`node --test tools/agents/tests/test_opencode.mjs`, `node --test tools/agents/tests/test_pi.mjs` and `python3 tools/loops/tests/test_loops.py`.
These exercise real guard processes, payload normalization, patch paths, failure decisions,
checkpoint invalidation, process deadlines, turn caps and issue severity routing.

Native qualification uses both discovery and witnessed tool dispatch. Codex needs a trusted project
and enabled hook sources; an untrusted layer being ignored is expected. OpenCode requires 2.1.4+
V2 domain callbacks: legacy function exports can appear in discovery without executing.

Real model-driven qualification is separate: it must show actual file changes and a witnessed
native guard denial in a disposable repository, not merely an agent's completion statement.
The [dated OpenCode experiment](../references/opencode-context-qualification.md) covers a native
278k-input call and refusal of an over-budget tool continuation in an isolated primary-HTTP profile.
No full 250k handover/compaction cycle or absolute Æion Factory admission ceiling is claimed. Local hook failures
can be advisory in some native events; retain native sandbox/permissions and check actual dispatch.
Hosted/cloud orchestration and optional scheduled native actions require separate qualification.

Devin is not yet qualified live: no Devin CLI ran in the change that added it. The hook file shape,
tool names, `DEVIN_PROJECT_DIR` and the block decision follow Devin's documentation and two public
integrations verified on Devin 3000.11.3. To qualify, in a disposable clone ask Devin to `cat .env`
and to edit a file: the first must be refused with the guard's reason, the second must name the
covering doc. Devin cloud sessions do not read `.devin/` and are not covered.

Pi is not yet qualified live either: no Pi ran in the change that added it. The events, results and
tool inputs follow the 1.4.0 docs and its published type declarations (`types.d.ts`, the tool schemas).
Unverified: that a thrown `before_agent_start` handler stops the run (the tool guards refuse anyway),
and that symlinked `.agents/skills` folders are followed. Qualify it like Devin with `tools/agents/run
pi`: `cat .env` and a read of that file refused with the guard's reason, an edit naming its covering
doc, and `/compact` cancelled until the checkpoint passes.

Droid is not yet qualified live either. docs.factory.ai was unreachable from the container that
added it, so the payload shape, tool names and `$FACTORY_PROJECT_DIR` follow search excerpts of
its hooks reference and public Droid hook integrations. Unverified: `ApplyPatch`'s input field
(an unknown field is refused, failing closed) and whether Droid also loads `.claude/` hooks.
Qualify it like Devin: `cat .env` refused with the guard's reason, an edit naming its covering doc.

Antigravity is not yet qualified live either; antigravity.google was unreachable from the
container that added it. The `toolCall` payload, `run_command`'s `CommandLine`, the decisions and
`.agents/hooks.json` follow the CLI changelog, a CLI issue quoting a real 1.4.4 payload and
search excerpts of the hooks page. Unverified: the exact case of the file tools' path fields
(an unknown field on a mapped file tool is refused), whether `StartLine` is 1-based, the Stop answer, and whether the IDE runs
workspace hooks (a forum report says its PostToolUse did not fire). A hook that crashes or
times out blocks the call. Qualify it with `agy`: `cat .env` and a view of that file refused
with the guard's reason, and an edit naming its covering doc; then repeat in the IDE.

OpenCode 2.1.4 is the qualified V2 target. Legacy 1.19.4 can discover skills but does not dispatch
these V2 callbacks; do not claim its guards are working from discovery alone. The plugin is a
directory with a default id/setup entrypoint and uses no SDK dependency.

OpenCode consumes a verified receipt before each compaction attempt. A retry must verify a new
checkpoint; it never silently reuses a receipt from an earlier compaction. The plugin imports only
Node built-ins and does not bundle an unused SDK or its dependency graph.

Malformed, non-object or oversized native input exits 2 without echoing the payload. A generic
stop JSON object with exit 0 is insufficient for a Codex PreToolUse decode failure.

On 2026-10-26, real disposable model tasks passed with native Codex and OpenCode 2.1.4 using
paid `opencode-go/deepseek-v4.1-flash`: source, owning doc and task state changed, guard refusals
were witnessed, and independent documentation/diff checks passed. OpenCode's denied call had
no completed-tool event. This qualifies bounded tool dispatch, not long-context admission.
Run disposable repositories outside a configured ancestor project: OpenCode inherits parent
configuration and can select that ancestor's plugin instead of the instrumented local copy.
