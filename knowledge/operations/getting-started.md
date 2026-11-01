---
type: Runbook
title: "Getting started with Æion Factory"
description: "First-run setup, new and existing projects, managed launch commands and dsh troubleshooting."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.6
  at: 2026-10-29
---

# Getting started

[Back to the overview](../../README.md) · [Agent compatibility and limits](agent-compatibility.md)

The launcher installs nothing. Install and connect your chosen agent separately, then trust the
project and approve its hooks as required below. The optional Git hooks and architecture tools
are described in [the overview](../../README.md#optional-tools).

## Prepare your agent

Git and **Python 3.12+** for the checks and hooks. Shell tools support macOS, Linux and WSL.
The recommended architecture baseline also needs **Node 18+** and **Chrome/Chromium** (Python
3.14.1 excluded for its pins); it is installed only when you say yes. Install `gh` for the GitHub
PR workflow and your chosen agent separately:

- [Claude Code](https://code.claude.com/docs/en/setup)
- [Codex](https://learn.chatgpt.com/docs/cli)
- [OpenCode V2](https://opencode.ai/v2/docs/) — 2.1.4+ for Æion Factory's native plugin
- [Pi](https://github.com/earendil-works/pi) — 1.4.0+ for Æion Factory's extension
- DeepSeek Harness (`dsh`) — 0.2.1+, loads `.dsh/` through `tools/agents/run dsh`
- [Devin CLI](https://docs.devin.ai/cli/extensibility) — reads `.devin/`, `AGENTS.md` and `.agents/skills`
- [Droid](https://docs.factory.ai/cli/configuration/hooks-guide), the CLI of Factory (factory.ai), a separate
  product — reads `.factory/settings.json`, `AGENTS.md` and `.agents/skills`
- [Google Antigravity](https://antigravity.google/docs/hooks) (`agy` CLI or IDE) — reads
  `AGENTS.md`, `.agents/skills` and `.agents/hooks.json`

Keep authentication, provider and model choices in the agent's native user settings. Never
commit credentials to the project.

For an existing Æion Factory checkout, use the first-run preparation in step 2 of
[New project](#new-project) without resetting its release metadata. Check hook loading as described
in step 3. A present configuration file alone does not prove the hooks are active.

## New project

1. [Create a repository from this template](https://github.com/OualidGuennif/aeion-factory/generate),
   then clone your new repository and open its folder.
   Reset the copied release metadata and tasks: `tools/release/release --new-project` (version 0.1.0, an
   empty changelog, one task: adapt the factory to this project).
2. Prepare your harness (once), then start it in that folder:

   | Harness | Start | What to do first |
   | --- | --- | --- |
   | Claude Code | `claude` | Trust the folder. Hooks (`.claude/settings.json`) and skills load on their own; check with `/hooks`. |
   | Codex | `codex` | Trust the project, enable its hooks in `/hooks`, then restart Codex. Skills come from `.agents/skills`. |
   | OpenCode 2.1.4+ | `opencode` | Connect your provider in OpenCode. The root `opencode.json` and `.opencode/plugins/factory/` load on their own; on a database conflict, `tools/agents/run opencode --isolated`. |
   | Pi 1.4.0+ | `pi` | Accept the trust prompt, so `.pi/extensions/factory/` loads (the startup list names `factory`). Connect your provider in Pi. |
   | dsh 0.2.1+ | `tools/agents/run dsh` (web UI) | The launcher adds `--patch .dsh/factory.patch.yml`, which loads the adapter; skills come from `.agents/skills`. Connect your provider in dsh. Ports, option order and background servers: [dsh in detail](#deepseek-harness-dsh-in-detail). |
   | Devin CLI | `devin` | Approve the project hooks (`.devin/`). |
   | Droid (factory.ai) | `droid` | Approve the project hooks (`.factory/settings.json`). |
   | Google Antigravity | `agy` | Trust the folder; hooks come from `.agents/hooks.json`. |

3. Check the hooks: ask the agent to run `cat .env`. The guard must refuse it and name its rule. If it runs, the hooks are not loaded: redo step 2.
4. Give the agent this setup request:

   > Read AGENTS.md, README.md and efficiency/00-EFFICIENCY.md. Prepare Æion Factory for this new
   > project: describe the project and owner, add its actual build/test commands, adapt the
   > architecture spec and analysis scope/views, and configure my chosen agent's native setup.
   > Run the checks. Ask me before enabling the Git hooks and before installing the recommended
   > Graphify/Archify baseline; tell me what it installs first. Keep one maintained source for
   > instructions, Knowledge and skills. Report anything that still needs configuration. Wait for
   > approval before implementing application features.

5. Say yes to the Git hooks, Graphify and Archify unless your policy forbids them (see [optional tools](../../README.md#optional-tools)).
6. From then on, start work with the managed launcher (`tools/agents/run <harness>`, below). Configure
   [GitHub main protection](github-protection.md) in the new repository;
   GitHub settings are not copied by templates.

## Existing project

1. Open your **existing project folder** with your harness. Keep its current instructions,
   configuration, tests and Git history.
2. Make a local reference copy of Æion Factory, or point the agent at a reference folder you already
   have:

   ```bash
   git clone https://github.com/OualidGuennif/aeion-factory.git ../aeion-factory-reference
   ```

3. Give the agent this adoption request, replacing the reference path:

   > Read ../aeion-factory-reference/AGENTS.md, efficiency/00-EFFICIENCY.md and the adopt skill.
   > Inspect this project's existing instructions, docs, CI, skills and hooks first. Propose the
   > smallest adoption plan, one phase at a time. Merge useful Æion Factory pieces into what exists;
   > preserve my project's authority, conventions and working tools. Include native setup for my
   > agent, linked specs and relevant checks; offer the Git hooks and the recommended
   > Graphify/Archify baseline and ask me before installing anything. Wait for my approval before
   > changing files.

4. Approve the fitting phases, validate each one and deliver through your project's PR workflow.
   This first session has no Æion Factory hooks yet: they arrive with the phase that copies your
   harness's native files. Once that phase is merged, restart the harness and do what it needs:

   | Harness | Files the adoption brings | After the merge |
   | --- | --- | --- |
   | Claude Code | `.claude/settings.json` hooks, `.claude/skills/` (merged with yours) | Restart; check `/hooks` |
   | Codex | `.codex/config.toml`, `.codex/hooks.json`, `.agents/skills` links | Trust the project, enable the hooks in `/hooks`, restart |
   | OpenCode | `opencode.json` (merged with yours), `.opencode/plugins/factory/` | Restart; reconnect the provider if you use `--isolated` |
   | Pi | `.pi/extensions/factory/`, `.agents/skills` links | Restart from the project root and accept the trust prompt |
   | dsh | `.dsh/`, `.agents/skills` links | Start with `tools/agents/run dsh [web\|headless]`; see [dsh in detail](#deepseek-harness-dsh-in-detail) |
   | Devin, Droid, Antigravity | `.devin/`, `.factory/`, `.agents/hooks.json` | Approve the project hooks or trust the folder |

5. Check the hooks as in a new project (step 3), then say yes to the Git hooks, Graphify and Archify
   unless your policy forbids them. Use [the adoption guide](../../efficiency/00-EFFICIENCY.md) and
   [runtime setup](agent-compatibility.md) for exact requirements.

## Start a prepared project

Run these from the repository root. Additional arguments are native CLI arguments.

| Agent | Command | Configuration |
| --- | --- | --- |
| Claude Code | `tools/agents/run claude` | Existing `.claude/settings.json`, hooks and skills |
| Codex | `tools/agents/run codex` | Trusted `.codex/config.toml` / `hooks.json`, shared `.agents/skills` |
| OpenCode | `tools/agents/run opencode` | Root `opencode.json`, native V2 plugin in `.opencode/plugins/factory/` |
| Pi | `tools/agents/run pi` | Extension in `.pi/extensions/factory/`, loaded once the project is trusted |
| dsh | `tools/agents/run dsh [web\|headless]` | Plugin in `.dsh/plugins/factory/`, loaded by `.dsh/factory.patch.yml` |
| Devin CLI | `tools/agents/run devin` | `.devin/hooks.v1.json` and `config.json`, `AGENTS.md`, shared `.agents/skills` |
| Droid (factory.ai) | `tools/agents/run droid` | `.factory/settings.json` hooks, `AGENTS.md`, shared `.agents/skills` |
| Google Antigravity | `tools/agents/run antigravity` | `.agents/hooks.json`, `AGENTS.md`, shared `.agents/skills` |

The launchers enter the project root and check the architecture baseline for the current commit;
without one they recommend it and continue. The original Claude entry point, `tools/context/run`,
also remains available.

### DeepSeek Harness (dsh) in detail

dsh needs more care than the other agents: it loads a project's plugins only from a patch overlay passed
on its command line, and its profiles differ in what a plugin may reach.

- **Profiles.** dsh 0.2.1 ships `web` (its interactive chat, in the browser), `headless` (one task, then
  exit) and `desktop` (run only by the DeepSeek Harness app). There is no `tui` profile:
  `dsh --profile tui` fails with `profile "tui" does not exist`. The desktop app does not load the patch,
  so its sessions are not guarded; use `web`.
- **Starts.** From the root, `tools/agents/run dsh` starts `web` and `tools/agents/run dsh headless "<task>"`
  answers one task (`--session-id <id>` continues a session). From a subfolder, or with `dsh` itself, pass
  the patch: `cd demo && dsh web --patch ../.dsh/factory.patch.yml`.
- **Option order.** `--patch` is a launcher option: put it right after the profile, before the app's own
  options. In `dsh web --no-open --patch ...` the launcher hands `--patch` to the web app, which fails with
  `unknown option '--patch'`. Write `dsh web --patch <file> --no-open --port 0 ...`.
- **Port.** `web` listens on 3080. A `dsh web` already running (a background server, another project)
  makes a second one fail with `EADDRINUSE`; add `--port 0` for a free port.
- **Headless.** No browser, no port: from the project (or a subfolder with the patch), each call answers
  one task. `--json` prints the events, the first with the `sessionId`; `--session-id <id>` continues it.
  ```bash
  cd demo && dsh headless --patch ../.dsh/factory.patch.yml --json "$(cat start/dsh/START.md)"
  dsh headless --patch ../.dsh/factory.patch.yml --session-id <id> "continue"
  ```
- **Sessions are guarded by their own folder.** The plugin finds `tools/agents/hook.py` above each
  session's working directory, not the launch folder; a session outside an Æion Factory project is left
  alone.
- **Startup warning.** In `web`, dsh prints `aeion-factory-compaction ... pending (waiting for service:
  compaction)`. That is expected: web keeps compaction inside each agent preset, out of a plugin's reach,
  while the guards (entry `aeion-factory`) run. `headless` loads both entries.
- **Compaction.** Past 250k with a verified handover, `headless` compacts by itself; in `web` the agent asks
  you to type `/compact`, and the plugin sees the token count fall and resumes the session from its
  handover.
- **Check it is loaded.** Ask the agent to run `cat .env`: it must be refused by
  `.claude/hooks/guard-bash.py`. If it runs, the patch is not loaded or the session is outside the project.
- **Provider and versions.** Connect your provider in dsh's own settings. `npx @deepseek-ai/dsh` may run
  another version than an installed `dsh` (`dsh --version`); both need 0.2.1+.

Details: [agent compatibility](agent-compatibility.md).
