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
are described in [the overview](https://github.com/OualidGuennif/aeion-factory/blob/v2.1.1/README.md).

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
   empty changelog, one task: adapt the factory to this project; the factory's `demo/` is removed).
2. Prepare your harness (once), then start it in that folder:

   | Harness | Start | What to do first |
   | --- | --- | --- |
   | Claude Code | `claude` | Trust the folder. Hooks (`.claude/settings.json`) and skills load on their own; check with `/hooks`. |
   | Codex | `codex` | Trust the project, enable its hooks in `/hooks`, then restart Codex. Skills come from `.agents/skills`. |
   | OpenCode 2.1.4+ | `opencode` | Connect your provider in OpenCode. The root `opencode.json` and `.opencode/plugins/factory/` load on their own; on a database conflict, `tools/agents/run opencode --isolated`. |
   | Pi 1.4.0+ | `pi` | Accept the trust prompt, so `.pi/extensions/factory/` loads (the startup list names `factory`). Connect your provider in Pi. |
   | dsh 0.2.1+ | `tools/agents/run dsh` (web UI) | The launcher loads the adapter; connect your provider in dsh. [dsh in detail](#deepseek-harness-dsh-in-detail) |
   | Devin CLI | `devin` | Approve the project hooks (`.devin/`). |
   | Droid (factory.ai) | `droid` | Approve the project hooks (`.factory/settings.json`). |
   | Google Antigravity | `agy` | Trust the folder; hooks come from `.agents/hooks.json`. |
   | Grok | `grok` | Trust the folder so `.grok/hooks/factory.json` loads. The Claude budget hook ignores a Grok envelope. |

3. Check the hooks: ask the agent to run `cat .env`. The guard must refuse it and name its rule. If it runs, the hooks are not loaded: redo step 2.
4. Give the agent this setup request:

   > Read AGENTS.md, README.md and efficiency/00-EFFICIENCY.md. Prepare Æion Factory for this new
   > project: describe the project and owner, add its actual build/test commands, adapt the
   > architecture spec and analysis scope/views, and configure my chosen agent's native setup.
   > Run the checks. Ask me before enabling the Git hooks and before installing the recommended
   > Graphify/Archify baseline; tell me what it installs first. Keep one maintained source for
   > instructions, Knowledge and skills. Report anything that still needs configuration. Wait for
   > approval before implementing application features.

5. Say yes to Graphify and Archify unless your policy forbids them, and turn on the team git flow when the project has a remote and reviews (see [optional tools](https://github.com/OualidGuennif/aeion-factory/blob/v2.1.1/README.md)).
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
   | Grok | `.grok/hooks/factory.json` | Trust the folder; `/hooks` lists it. The Claude budget hook ignores a Grok envelope |

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
| Grok | `tools/agents/run grok` | `.grok/hooks/factory.json`, `AGENTS.md`, shared `.claude/skills` and `.agents/skills` |

The launchers enter the project root and check the architecture baseline for the current commit;
without one they recommend it and continue. The original Claude entry point, `tools/context/run`,
also remains available.

### DeepSeek Harness (dsh) in detail

dsh loads the factory only through a patch on its command line; `tools/agents/run dsh` adds it.

- **Start.** `tools/agents/run dsh` opens `web`; `tools/agents/run dsh headless "<task>"` answers one
  task (`--session-id <id>` continues it). The desktop app does not load the patch, and there is no
  `tui` profile.
- **Outside the root.** Put the patch right after the profile:
  `dsh web --patch <root>/.dsh/factory.patch.yml --port 0` (`--port 0` avoids a second server on 3080).
- **Compaction.** Past 250k with a verified handover, dsh compacts and resumes from the handover. If it
  does not, stop the session and start a new one from the handover. In `web`, the startup line
  `aeion-factory-compaction ... pending` is expected.
- **Check it is loaded.** Ask the agent to run `cat .env`: the guard must refuse it.
- **Versions.** dsh 0.2.1+ (`dsh --version`); connect your provider in dsh's own settings.

Details: [agent compatibility](agent-compatibility.md).
