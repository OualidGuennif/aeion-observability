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
  - resource: ../../tools/agents/pi-rpc
    title: "Headless Pi RPC runner"
  - resource: ../../tools/agents/tests/test_pi_rpc.py
    title: "Fake-RPC tests for the headless Pi RPC runner"
  - resource: ../../tools/agents/adapter-check
    title: "Connector copy drift check"
  - resource: ../../tools/agents/dsh-install
    title: "Tag-pinned desktop plugin install"
  - resource: ../../tools/agents/template-update
    title: "Project update to a new release"
  - resource: ../../tools/agents/connectors.py
    title: "The connector and merge file lists"
  - resource: ../../tools/agents/refs.py
    title: "Reading a git reference without a checkout"
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
  - resource: ../../.pi/README.md
    title: "Pi integration and its headless limitation"
  - resource: ../../.opencode/README.md
    title: "OpenCode integration and its live note"
generated:
  by: aeion-factory/1.6
  at: 2026-11-02
---

# Agent compatibility

AGENTS.md, Knowledge, task state, checker commands and the reviewed PR workflow are shared.
Claude Code remains the original integration. Codex, OpenCode, Pi, dsh, Devin, Droid and Antigravity use their
documented native configuration and small adapters to the existing guards/checkpoints; copying a
directory does not establish loaded hooks or identical runtime guarantees. `tools/agents/run` stops
with one line naming a missing agent binary and the setup link, exit 1.

## Contract

- Keep existing `.claude/skills` as the maintained skill source. Codex discovers symlinked folders
  under `.agents/skills`; OpenCode already discovers the Claude-compatible paths.
- Codex local trusted projects enable `.codex/config.toml` and `.codex/hooks.json`. Its native
  auto-compaction threshold is 250000. Codex has no compaction tool and ends its turn on a refused
  compaction, so a compaction that comes before the verified handover runs, and closure is owed right
  after it. Its rollout is not a stable token API.
- OpenCode 2.1.4+ loads root `opencode.json` and `.opencode/plugins/factory/index.js`. The plugin reads each
  step's tokens (`session.step.ended`) and compacts itself at 250k once the handover is verified. A live
  2.2.0 run on 2026-11-02 compacted a 272k step on a turn with two tool calls; a one-tool turn can miss the
  trigger because that event arrives after the tool hook, so the next tool or turn sees it. See
  [the OpenCode integration note](../../.opencode/README.md).
- Pi 1.4.0+ reads `AGENTS.md`/`CLAUDE.md` from its folder and every parent, and project
  `.agents/skills` from its folder or a parent, so the shared rules and skills need no copy. It loads
  `.pi/extensions/factory/index.js` from **its start folder only**, once the project is trusted; started
  elsewhere (`demo/`), pass it explicitly: `pi -e ../.pi/extensions/factory/index.js`. A headless run
  (`pi -p`) is never a trusted project, so discovery loads nothing there: pass the extension explicitly,
  `tools/agents/run pi -p -e .pi/extensions/factory/index.js "task"`, and add `--mode json` when a caller
  needs the event stream. Without `-e`, a headless Pi session runs with no Æion Factory hook at all and
  nothing in the transcript says so. The extension sends
  `before_agent_start` (once per session, and again after a compaction) as SessionStart, `tool_call` as
  PreToolUse (`{block: true, reason}`, also on any hook failure), `tool_result` as PostToolUse (feedback
  appended, `structuredContent` kept) and `session_before_compact` as PreCompact (`{cancel: true}` and a
  notification without a verified handover) to `tools/agents/hook.py pi`. `bash` and `powershell` are
  Bash, `read`/`edit`/`write`/`grep` name their file in `path`, `find` and `ls` are Glob and LS, and an
  unknown tool carrying a `command` string is a shell call. `tools/agents/run pi` requires 1.4.0+.
  Its compaction aborts the running turn, so once it is done the extension sends a message that resumes
  the task from the handover. `tools/agents/run pi rpc` starts the factory's headless RPC runner instead
  (`tools/agents/pi-rpc`): one `pi --mode rpc` process with the extension, one prompt over JSONL, and
  the run waits through the settlement compaction and the resumed run, so headless Pi can compact and
  continue without a TUI; a Pi that exits before reading the prompt is one `pi-rpc:` line, exit 1.
  Print/JSON mode still does not compact (see the Pi note).
  The extension sends `ctx.getContextUsage()` to the shared rule and calls `ctx.compact()` at 250k once
  the handover is verified; the 250k alert names the checkpoint command, and closure admits a project's
  Markdown docs. `agent_before_settle` sends Stop: a sign-off finding becomes a displayed
  `custom_message` entry with `continue: true` (one more request); the hook shows each finding once, so
  the next settlement passes. A terminal stop (`continue: false`: a stopped run, invalid or unavailable
  usage) settles at once and shows its reason in the UI, never as another request. A closure refusal
  repeats at most three times and then settles with the
  reason in the UI, so one alert cannot spin forever. The guards are qualified live headless (2026-11-01);
  the 250k compaction is not (2026-11-02): the extension's `ctx.compact()` aborts the headless run and its
  error handler exits on a stale ctx, so no compaction entry is written, and `agent_before_settle` sends
  Stop without `observed_tokens`. See [the Pi note](../../.pi/README.md) and
  [Qualification and limits](#qualification-and-limits).
- Token feedback (narration between tools, full-file rewrites; advisory, never blocking) covers
  Claude Code natively and Codex through its rollout transcript. Devin, Droid and Antigravity pass
  no transcript the hook can read and the OpenCode and Pi extensions pass no assistant text, so they get the
  written rule in `AGENTS.md` only; the adapter stays silent for them and keeps working.
- In a plain folder without git, every hook command falls back from `git rev-parse --show-toplevel`
  to the current folder, so the adapters run where the agent starts. Limit: a plain folder started
  from a subfolder, or nested in another repository, does not find `tools/agents/hook.py`; Codex and
  Antigravity then refuse every tool call (fail closed). Start the agent at the project root.
  Inside a git repository a subfolder such as `demo/` works: the hook commands resolve the git root,
  and the OpenCode and Pi extensions run the hooks three folders above their own file, never a
  `tools/agents/hook.py` found above a session's folder (one could be planted); with none there, every call is refused.
- Patches and file filters, every harness: a patch header (`*** Add File:`, `Update File`,
  `Delete File`, `Move to`) is read as harness parsers read it, trimmed, in any case. An empty path or
  one with a colon, any other `*** Word:` header, or two patch texts is refused. On every non-shell tool,
  each string at any depth under `include`, `glob`, `globPattern`, `filePattern` or `includePattern`
  (any case, `_`/`-` ignored, plurals too; never `pattern`, the search regex) meets the Grep `glob`
  check ([security](../policies/security.md)); OpenCode's grep filter is `include`.
- Both adapters enforce supported Bash/path refusals, edit feedback and a verified handover,
  and a Pi compaction the checkpoint did not verify still runs and owes that closure after it
  instead of trapping the session at its window; the first refused compaction creates the skeleton to fill.
  Native token stops and strict pre-request 300k admission are unqualified.
- dsh (DeepSeek Harness, `dsh` 0.2.1+) reads `AGENTS.md`/`CLAUDE.md` and `.agents/skills` natively. It
  loads project plugins only from a patch: `tools/agents/run dsh [web|headless]` passes
  `--patch .dsh/factory.patch.yml`, which loads `.dsh/plugins/factory/index.js` (the guards) and
  `compaction.js` (compaction, shared through `seam.js`); a dsh started without it is unguarded.
  - **Guards.** Each tool call goes to `tools/agents/hook.py dsh` as PreToolUse (a call without an agent
    is refused), with `ctx.tokenMeter.measure(session).totalTokens` as usage; `tools/post-execute` sends
    PostToolUse and `agent/turn-stopping` sends Stop. The plugin finds the hook above each session's own
    directory, so one web server guards every factory project and leaves other folders alone. It runs
    that project's hooks only if it is the project the plugin ships in (the `tools/agents/run dsh`
    overlay) or one the profile trusts: `tools/agents/dsh-install --trust PROJECT` lists it in
    `aeion-factory.trusted` beside the profile's link, read on each call. Any other project's calls are
    refused with that command, so a planted `tools/agents/hook.py` never runs. `bash` is
    Bash, `read`/`write`/`edit` name `file_path`, `str_replace_editor` is Edit (Read for `view`), and
    `glob`/`grep` are Glob/Grep.
  - **Messages.** dsh cannot add prompt text, so the start context is steered on the first guarded call.
    Every steered message carries an `id` and `role: "user"`, without which dsh refuses to reopen the
    session. A sign-off finding is steered once; `continue: false` ends the turn and is never steered.
  - **Compaction.** After a verified handover, the next `agent/pre-step` sends PreCompact and compacts
    (headless: the root service; web: the `/compact` command once the agent is idle), then resumes from
    the handover. A profile with no compaction service gets the advisory gate, and a token measure that
    falls by over half marks dsh's own compaction as SessionStart `source: compact`. dsh's pressure
    compaction (about 55% of a 1M window) is not refused. If compaction does not run, the messages say to
    stop and resume from the verified handover. Live 2026-11-02: headless compacted at 250k and resumed.
  - **Sandbox.** It writes only below the launch folder: started in `demo/`, it cannot write the root's
    `.git` or `work/`, so start it at the root. Move home-folder state into the workspace, e.g.
    `DOCKER_CONFIG=$PWD/.docker` for `docker compose`.
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
  `run_command` (`CommandLine`) to Bash, `view_file` and `read_file` to Read, `write_to_file` and
  `write_file` to Write, `replace_file_content`/`multi_replace_file_content`/`edit_file` to Edit and
  `grep_search` to Grep. For any
  tool, including MCP tools, every nonempty string at any depth under an argument whose name,
  ignoring case and `_`/`-`, ends in path, file, dir, directory or uri, or their plurals
  (`AbsolutePath`, `TargetDirectories`, `file_path`, `Uri`; a `file:` URI is decoded to its path),
  goes through the path guard; `view_code_item`'s `NodePaths` are code symbols and are skipped. A
  mapped file tool with none is refused. Not recognized: other names (`target`, `Url`), text typed
  into a running command (`send_command_input`) and Windows paths. `view_file` and `read_file`
  `StartLine`/`EndLine` become the intake window; `grep_search` with `MatchPerLine: false` lists
  names only. For any tool, every string at any depth under an argument whose name ends in
  include, glob or pattern, or their plurals (`Includes`, `IncludePattern`, `file_pattern`), goes
  through the same check as Claude's Grep `glob` filter ([security](../policies/security.md)),
  with its limits; a non-string filter is refused. Any tool with a `CommandLine` goes through the
  shell guard, as does a `command` or `commandLine` argument in any case; a call with two is
  refused. `Cwd` or `workdir` in any case (a `file:` URI decoded) is the shell's directory; two
  or a non-string one are refused. On a shell call any other argument must be a flag or a
  number, since the guard cannot tell which one a tool runs in; a text, list or object is refused,
  except AGY 2.0's required `toolSummary` string, the line shown to the user, which is never run.
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
(`tools/agents/hook.py`), the context rule (`tools/context/budget.py`), the launcher and the headless
Pi RPC runner it dispatches to (`tools/agents/run` and `tools/agents/pi-rpc`), the Claude hooks, the dsh
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
tools/agents/adapter-check --root ../app --ref v1.8.4   # against a release, not this working tree
tools/agents/adapter-check --root ../app --ref main     # or a branch somebody works from
```

`connectors.py` also ships the two readers a project's check imports instead of re-implementing
them: `linked(root, relative)` returns the first path component below the root that is a symlink,
without following it, and `executable(mode)` reads the executable bit from either a git mode string
or a `stat` mode. A copy that predates them cannot answer a check that imports them.

It prints one line per connector: `ok`, `DRIFT` with both sizes and the exact `cp` that repairs it,
`UNWIRED` for a native config that names a `.py`, `.js` or `.sh` script which is not there (a `.json`
path, such as a credentials file in a deny rule, is not a script), `invalid` for a config that
is not valid JSON, `LINKED` for a connector or one of its parent folders that is a symlink, `MODE`
for a launcher that lost its executable bit, and `UNIDENTIFIED` with its line for a
`steer`/`inject`/`followup` call that carries no id and `UNROLED` for one that carries no role. A
connector the project does not carry is `absent`: listed under `--verbose`, and
a failure only under `--strict`, because a Claude-only project legitimately has no Pi extension.
Exit code 0 is clean, 1 is drift, broken wiring, a linked connector, a non-executable launcher, or
an unidentified/unroled steer, 2 is a bad root or the script's own copy.

A connector must be a regular file owned by the project. A symlink is reported as `LINKED` and
never followed: comparing the file it points at would call a file outside the project a match. The
same rule protects the update below, which refuses a linked destination instead of writing through
it. The executable bit is part of the contract: `tools/agents/run` is recorded as `100755` in the
release tree, and a copy that reads `0644` fails `MODE` even when every byte matches.

Configs a project merges with its own settings are not compared byte for byte —
`.claude/settings.json`, `.codex/config.toml`, `.devin/config.json` — but their commands are: every
script they name must exist. Run the check after adopting, after every factory upgrade, and in the
project's own CI — from a pinned factory checkout with `--root`, never from the copy inside the
project, which would compare the project with itself and pass; the factory's own run passes
`--self`. The factory runs it on itself in `tools/factory-tests`, which catches a
registration that points at a renamed or deleted module.

The same check refuses a connector that steers a message without an identity. dsh persists a
steered message and its loader then rejects the whole session for holding one it cannot name, so a
connector that omits the `id` turns every session it touched into history that will not reopen.
Every `steer({...})` the factory ships carries an `id`; a call without one is reported as
`UNIDENTIFIED <file> — steer() without an id at line N` and fails the check.

## Updating a project to a new release

An adopted project carries its own copies of the factory's files next to its own instructions,
settings and knowledge. An update must move every factory file the release changed, keep each edit
the project made, and leave the project's own text alone.

### Intent

Move a project from the factory release it adopted to another reference, deciding each file the
factory changed between the two, and each factory file the project still holds as an older
release's untouched copy, on its own, so a connector matches its release byte for byte, an
untouched factory file follows the release, a project edit survives, and a conflict or a project-owned
file goes to a human. The application's `VERSION` is not factory provenance: it is neither read as
the baseline nor written.

### Data sources

| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| `--from-ref`, else the project's `.aeion-factory` marker | the factory release or commit the project adopted | the caller; the last update or `release --new-project` | at each update |
| the factory's `vX.Y.Z` tags | every tagged tree's object ids, against the project's files | the releases | at each update: the inferred baseline, and the release an untouched older copy came from |
| the project's tree and git state | file bytes, executable modes, links, tracked changes, `develop`, `aeion.mode` | the project | at each update |
| the baseline and target trees | every changed file's bytes and git mode, the target's `CHANGELOG.md` | the factory | at each update |

### Inputs

```bash
tools/agents/template-update --ref v2.0.1 --root ../app --check
tools/agents/template-update --ref v2.0.1 --root ../app
tools/agents/template-update --from-ref v1.8.5 --ref main --root ../app
```

- `--from-ref`: the factory reference the project adopted. Optional: without it the tool reads the
  project's `.aeion-factory` (`<ref> [<commit>]`, the commit preferred because a branch moves), and
  without a marker it infers the release tag whose files the project matches best, newest on ties.
  A write on an inferred baseline needs every contract connector to match it; a partial match runs
  `--check` only. It is never read from the project's `VERSION`.
- `--ref`: the target tag, `main`, `develop` or a commit id.
- `--root`: the project that adopted the factory; `--repo`: the factory repository holding both
  references (default: the checkout the tool runs from). A project's own copy of the tool cannot
  see a newer release, so `--root` and `--repo` must differ and `--repo` must not hold an
  `.aeion-factory` marker: run it from the factory clone. That refusal comes before `--root` is
  checked, since a relative `--root` typed inside a project names a folder that does not exist.
- `--check` writes nothing; `--force` permits moving to an older factory release.

### Outputs

The header names the baseline and how it was found (`--from-ref`, `.aeion-factory` or
`inferred: <n>/<m> factory files and <c>/<k> connectors match`), a `MAJOR a.x → b.x` banner when the
major version grows, and the target's `CHANGELOG.md` sections newer than the baseline (80 lines at
most). Then one line per file, in these classes:

| Class | Files | Line |
| --- | --- | --- |
| contract | `connectors.CONTRACT` | `written`, `mode`, `skipped — not in <ref>`; `DRIFT`/`MODE` under `--check` |
| project-owned | `VERSION`, `CHANGELOG.md`, `.aeion-factory`, `work/`, `knowledge/`, `demo/` | never written; a changed `knowledge/` doc is `review <file>` |
| merge | `connectors.MERGE` (`AGENTS.md`, merged settings) | never written; `merge <file> — proposal: <path>` |
| three-way | every other changed file, and every factory file still an older release's copy | `updated` (the project kept the baseline, or an older release's copy: `— untouched since <tag>`), `added` (new, its folder exists), `removed` (deleted upstream, untouched here), `merged` (`git merge-file` was clean), `conflict` (left as it is, with a proposal), `review` (removed upstream but edited here, or a link the project changed), `link`, `mode` |

An update before 2.0.1 moved only the connectors, so a project can hold a factory file byte for byte
as an older release had it; such a file diffs from that release, not from the baseline, and takes
the target even when the factory left it alone since the baseline. Files the project deleted, and
new files in a folder the project never adopted, stay out and are counted on one `untouched` line.
A proposal (the three-way result, conflict markers included) is written under
`.aeion/template-update/<ref>/` on a write; that folder carries its own `.gitignore`, so a project
that does not ignore `.aeion/` never sees the proposals as files to commit. A `migrate` line names what
the owner must run for a release crossed, such as `git config aeion.mode team` for 2.0.0 when the
project has a `develop` branch and no team mode; the tool never runs it. A write ends by recording
`<ref> <commit>` in `.aeion-factory` and naming the verification and the commit.

Exit code 0 when nothing needs a human, 1 when a merge, conflict, review or migration remains (and,
under `--check`, when anything would change or the inferred baseline is partial), and 2 on a refusal:
`no such reference: <ref>`, `.aeion-factory names <ref>, unknown in <repo>`,
`baseline <tag> inferred: …; confirm it with --from-ref <tag>`, `no VERSION at the baseline <ref>`,
`<root> has uncommitted changes`, `not an adopted project: no factory connector in <path>`,
`refusing linked [connector] destination <path> below <root>`,
`refusing non-regular [connector] destination <relative>`, `refusing to downgrade <a> to <b>`, and
`refusing to update a project from its own repository <repo>; run template-update from the Æion
Factory clone` (its hint names `--root <project>` when `--root` is no folder).

### Invariants

1. The project's `AGENTS.md`, `knowledge/`, `CHANGELOG.md` and `VERSION` are never written —
   `test_writes_the_reference_and_keeps_the_project_text`,
   `test_the_application_version_is_never_written`, `test_knowledge_is_listed_never_written`.
2. `--check` writes nothing — `test_check_writes_nothing`.
3. Both references are validated and a branch is valid on either side —
   `test_a_branch_is_a_valid_reference`.
4. A downgrade needs `--force` —
   `test_it_refuses_a_downgrade`, `test_a_downgrade_with_force_is_allowed`.
5. The baseline comes from the flag, then the marker, then an exact inference; an unknown marker or
   a partial inference never writes — `test_the_marker_is_written_then_used`,
   `test_a_new_project_marker_names_its_release`, `test_an_unknown_marker_is_refused`,
   `test_an_exact_inference_writes`, `test_a_partial_inference_only_checks`.
6. Repeating the same from/to pair keeps naming an unpaid merge even when every connector matches —
   `test_a_merge_only_check_keeps_naming_the_merge`.
7. A linked destination file or parent, or a linked proposal folder, is refused before the first
   write — `test_a_linked_connector_is_refused_before_any_write`, `test_a_linked_parent_is_refused`,
   `test_a_linked_proposal_folder_is_refused`.
8. A created or repaired launcher carries the reference's executable mode —
   `test_a_missing_launcher_is_written_executable`,
   `test_a_launcher_that_lost_its_mode_is_repaired`.
9. A directory with no connector is not an adopted project, and a repository never updates itself
   (the factory, or a project running its own copy, even with a mistyped `--root`) —
   `test_it_refuses_a_project_with_no_connector`, `test_it_refuses_to_update_a_repository_from_itself`,
   `test_a_project_copy_names_the_factory_clone_before_a_mistyped_root`.
10. An untouched factory file takes the target, an edit merges, a conflict keeps the project's file
    with a proposal in a folder that ignores itself, and a file the project deleted stays deleted —
    `test_an_untouched_factory_file_takes_the_target`, `test_a_project_edit_merges_with_the_target`,
    `test_a_conflicting_edit_is_kept_with_a_proposal`, `test_a_file_the_project_deleted_stays_deleted`.
11. A write refuses tracked uncommitted changes, so the update is one revertible commit —
    `test_a_dirty_project_refuses_a_write`.
12. The notes, the major banner and a migration hint are printed, and the mode switch is left to
    the owner — `test_notes_major_and_the_mode_migration`.
13. A factory file the project holds as an older release's untouched copy takes the target, even
    when the factory left it alone since the baseline; an edited one is never caught up —
    `test_an_older_untouched_copy_takes_the_target`, `test_an_edited_older_copy_is_never_caught_up`.

### Determinism

The same project tree and references always give the same decisions and the same output: bytes,
object ids and modes come from git objects, `git merge-file` is deterministic, destination links are
checked before the first write, paths are sorted, and only the marker records the target commit.

### Acceptance checks

```bash
python3 tools/agents/tests/test_template_update.py
python3 tools/agents/tests/test_adapter_check.py
python3 tools/release/tests/test_release.py
tools/factory-tests
```

### Out of scope

- resolving a conflict or a merge file for the project: each gets a proposal, never an edit.
- running a migration step such as `git config aeion.mode team`: the owner runs it.
- fetching: the factory checkout must already hold both references (`git fetch --tags`).
- committing, pushing or opening a pull request; creating the tag: `tools/release/release` owns the version.

## Installing the desktop plugin at a tag

The desktop profile composes the factory plugin as `./aeion-factory/index.js` and
`./aeion-factory/compaction.js`, resolved inside the profile folder. A symlink from there into a
working tree makes the running app follow that tree: an uncommitted or broken edit reaches the app,
and no review can say which version ran. This installs from a release tag instead.

### Intent

Run the desktop app on a released tag rather than the working tree, so a dirty or broken `develop`
cannot reach it, and make the loaded tag checkable.

### Data sources

| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| git object store | every file of `.dsh/plugins/factory` at one tag | the release that made the tag | read at each install and check |
| `<profile>/aeion-factory` | the link that decides the loaded plugin | this tool | at install |
| `<profile>/cordis.patch.yml` | the module names the app loads | the dsh profile | never written here |

### Inputs

```bash
tools/agents/dsh-install [--tag vX.Y.Z] [--trust PROJECT ...] [--profile desktop] [--profile-dir PATH] [--repo PATH]
tools/agents/dsh-install --check   [--profile desktop] [--profile-dir PATH] [--repo PATH]
```

- `--tag`: an existing tag in the repository, the whole name (`v1.8.4`); annotated or lightweight.
- `--trust`: a project whose hooks the plugin may run (repeatable); its root must hold
  `tools/agents/hook.py`. It is recorded once, resolved, in `<profile>/aeion-factory.trusted`.
- `--profile`: a folder under the profile directory, default `desktop`.
- `--profile-dir`: default `~/.dsh/profiles`; a test passes its own temporary one.
- `--repo`: the repository the tag is read from, default this checkout.
- `--force`: replace an `aeion-factory` entry that is not a symlink, after moving it aside.

### Outputs

- Install writes `<profile>/vendor/aeion-factory-<tag>/` with the tag's files, then makes
  `<profile>/aeion-factory` a relative symlink to that folder. Prints `installed <tag> → <path>`.
- `--trust` prints `trusted <project>`, or refuses `<project> has no tools/agents/hook.py; …`.
- `--check` prints `ok <tag>` when every file matches the tag, otherwise one `DRIFT <file>` or
  `MISSING <file>` line per difference.
- Exit codes: 0 clean, 1 drift or an incomplete copy, 2 a refusal. Refusals name the condition:
  `no such tag: <tag>`, `tag <tag> has no .dsh/plugins/factory`, `no profile directory: <path>`,
  `not a git repository: <path>`, `<entry> is not a link; move it aside or pass --force`
  (with `--force`, a `aeion-factory.replaced` that already exists is itself refused), and from
  `--check`, `no aeion-factory link in <path>` and `link does not name a vendored tag: <target>`.

### Invariants

1. Every installed byte equals the tag's byte — `test_installs_the_tag_bytes`.
2. A second install of another tag repoints the link and keeps the earlier copy —
   `test_a_second_tag_repoints_the_link`.
3. A copy that fails leaves the previous link in place — `test_a_failed_copy_keeps_the_old_link`.
4. An unknown tag writes nothing — `test_unknown_tag_refuses`.
5. A non-link entry is refused, and `--force` overwrites nothing —
   `test_unmanaged_entry_refuses` and `test_force_refuses_a_second_displacement`.
6. `--check` fails on one hand-edited byte — `test_check_names_a_hand_edited_copy`.
7. `--check` fails on a link that does not name a vendored tag —
   `test_check_refuses_a_foreign_link`.
9. `--trust` records a project once, refuses one without hooks, and the plugin runs only trusted ones —
   `test_trust_records_a_project_once_beside_the_link`, `test_trust_refuses_a_folder_without_the_factory_hooks`, `test_dsh.mjs`.
8. `adapter-check` reports a `steer` call without an id —
   `test_steer_without_id_is_unidentified`, fails a copy that steers unidentified —
   `test_a_steering_copy_fails_the_check`, and passes the shipped adapters —
   `test_the_shipped_adapters_are_identified`.

### Determinism

deterministic: bytes come from git objects, the file list is sorted, and nothing is stamped with a
clock. `--force` renames to the fixed name `aeion-factory.replaced` rather than to a timestamp.

### Acceptance checks

```bash
python3 tools/agents/tests/test_dsh_install.py
python3 tools/agents/tests/test_adapter_check.py
tools/agents/adapter-check --self
tools/factory-tests
```

### Out of scope

- creating, signing or publishing the tag: `tools/release/release` owns that.
- installing any other harness or profile.
- repairing sessions whose stored messages already lack an id.
- proving a tag was reviewed, or that it is the newest release.

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

Pi is qualified live headless only through an explicit extension: `tools/agents/run pi -p --mode json
-e .pi/extensions/factory/index.js` injected the checkpoint profile (`Æion Factory pi checkpoint
profile`) into the session, which only the extension writes, and the bash guard then refused an
environment dump; without `-e`, discovery loads no extension in a headless run and the same session
was unguarded. Trust-based discovery and the interactive path remain unqualified. The events, results and
tool inputs follow the 1.4.0 docs and its published type declarations (`types.d.ts`, the tool schemas).
Unverified: that a thrown `before_agent_start` handler stops the run (the tool guards refuse anyway),
and that symlinked `.agents/skills` folders are followed. Qualify it like Devin with `tools/agents/run
pi`: `cat .env` and a read of that file refused with the guard's reason, an edit naming its covering
doc, and `/compact` cancelled until the checkpoint passes. A 1.9.2 re-run at 264k stopped cleanly at the gate with the verified handover (exit 0, no crash);
the one-shot print run cannot finish the summary, so headless Pi stops and the next session continues
from the handover. Interactive Pi compacts at settlement.

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

OpenCode 2.1.4 is the qualified V2 target; 2.2.0 also passed the 2026-11-02 live 272k compaction on a
two-tool turn. Legacy 1.19.4 can discover skills but does not dispatch these V2 callbacks; do not
claim its guards are working from discovery alone. The plugin is a directory with a default id/setup
entrypoint and uses no SDK dependency.

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

### Live 250k qualification, 2026-11-02

Method: clean v1.9.1 worktrees, real calls with `deepseek-v4.1-flash` (1M window), a 1.0–1.35 MB
context fill, a completed handover and a receipt created with
`python3 tools/context/budget.py checkpoint --session <key> --base HEAD --verify`, then one measured
turn. Versions: dsh 0.2.1-rc.5 headless, Pi 1.4.0, OpenCode 2.2.0, Python 3.15.2.

| Harness | Live result |
| --- | --- |
| dsh headless (patched) | 1 MB user turn; the plugin's meter crossed 250k; compacted, epoch 1, resumed from the handover. PASS. |
| OpenCode 2.2.0 | 272k-token step; a two-tool turn compacted (epoch 1, RECOVERING). A one-tool turn missed it: `session.step.ended` arrived after `tool.execute.after`, so the next tool or turn triggers. |
| Pi 1.4.0 headless | 264,275 measured (1.9.2 re-run). The gate latched `HANDOVER_REQUIRED`; Stop now carries `observed_tokens`; the run exits 0 with a stderr notice and no compaction entry, and the verified handover is the next session's start. The 1.9.1 crash (mid-turn `ctx.compact()`, stale ctx, exit 1) is fixed. Headless auto-compaction remains unavailable in print mode; TUI compaction at settlement is implemented but not live-tested. |
| Pi via `tools/agents/pi-rpc` | `tools/agents/run pi rpc --provider opencode-go --model deepseek-v4.1-flash --prompt-file <1.35 MB prompt>`. A 1,350,333-character prompt reached the gate; the model filled the handover and its checkpoint verified; at settlement the extension compacted (`tokensBefore` 288,668; usage input 262,002, output 1,753; cost $0.0403521), the `onComplete` resume message started a new run in the same process, and that run read the handover and continued. The runner was stopped during the resumed work, so this run does not prove exit 0; the fake-RPC compaction test and a real short RPC call cover the exit path. The compaction entry's `fromHook: false` means Pi generated the summary (the extension supplied none), not that Pi started the compaction. PASS for headless RPC compaction and resume. |

Limits: headless CLIs only (the TUI path was not re-tested), fresh receipts (the stale-receipt
branch is covered by the deterministic suites, not this run), one model/provider, no clean exit
observed on the compaction run, and no Devin, Droid or Antigravity run. The Pi 1.9.2 fix remains the
print-mode clean stop; headless auto-compaction is provided by the RPC runner above, and the
limitation and workaround are in [the Pi note](../../.pi/README.md).
