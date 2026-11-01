---
type: Runbook
title: "Build and test"
description: "Every gate of this repository, where to run it, and the language servers."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: ci
    resource: ../../.github/workflows/ci.yml
    title: "CI"
  - id: lsp
    resource: ../../tools/claude-plugins/native-lsp/.lsp.json
    title: "Language-server registrations"
  - resource: ../../.claude/hooks/after-edit.py
    title: "after-edit.py, which names this doc as its spec"
  - resource: ../../.claude/hooks/project_files.py
    title: "project_files.py, which names this doc as its spec"
  - resource: ../../.claude/hooks/session-start.py
    title: "session-start.py, which names this doc as its spec"
  - resource: ../../.claude/hooks/sign-off.py
    title: "sign-off.py, which names this doc as its spec"
  - resource: ../../tools/claude-plugins/deno-lsp/scripts/deno-lsp
    title: "deno-lsp, which names this doc as its spec"
  - resource: ../../tools/claude-plugins/native-lsp/scripts/jdtls-launch
    title: "jdtls-launch, which names this doc as its spec"
  - resource: ../../tools/claude-plugins/native-lsp/scripts/tsc-lsp
    title: "tsc-lsp, which names this doc as its spec"
  - resource: ../../tools/efficiency/bundle
    title: "bundle, which names this doc as its spec"
  - resource: ../../tools/factory-tests
    title: "factory-tests, which names this doc as its spec"
  - resource: ../../tools/git-hooks/pre-commit
    title: "pre-commit, which names this doc as its spec"
  - resource: ../../tools/knowledge/orphans
    title: "orphans, which names this doc as its spec"
  - resource: ../../tools/knowledge/stale
    title: "stale, which names this doc as its spec"
---

# Build and test

CI action revisions are pinned to upstream commit SHAs; review upstream changes before updating them.

The standalone efficiency bundle includes the CRAFTED principles as well as the seven chapters.
Rebuild it with `tools/efficiency/bundle` after editing those sources or `CREDITS.md`; CI rebuilds
it and fails when the committed bundle differs.

| Layer | Gate | From |
| --- | --- | --- |
| Knowledge | `tools/knowledge/knowledge-check` | the root |
| Knowledge freshness | `tools/knowledge/stale`: a `review_after` date that has passed | the root |
| Knowledge reachability | `tools/knowledge/orphans`: a document nothing links | the root |
| Docs and code links | `tools/knowledge/doc-links` (`--diff origin/develop` before a push) | the root |
| Comments, file size, caps | `tools/repo-health/repo-health` | the root |
| The factory's own test suites (hooks, tools, evals, push gate, release, context, analysis and graph queries, adapters including the OpenCode, Pi and dsh plugins, connector drift, loops) | `tools/factory-tests` (each suite also runs alone; the script lists them) | root; Node 18+ |
| Connector copies | `tools/agents/adapter-check` (`--root` for a project that adopted the factory) | the root |
| Efficiency bundle | `tools/efficiency/bundle`, then `git diff --exit-code efficiency/efficiency-bundle.md` | the root |
| Source analysis (CI on every main update; local run recommended) | `tools/architecture/refresh --target HEAD --base origin/main` after committing | pinned tools installed on the user's yes, Node and Chrome required |
| Your code | add your build, lint and test commands here, copied from CI | |

`stale` and `orphans` reject a missing root or `knowledge/` directory with a nonzero exit;
`orphans` also requires `knowledge/index.md`. An absent tree is not a successful empty check.
A valid knowledge directory with no dated documents still passes `stale`.

The pre-commit (`git config core.hooksPath tools/git-hooks`) runs `knowledge-check`, `doc-links`
and `repo-health`. The pre-push refuses a push of `develop` without a recorded `Review: OK`
and any direct push to `main`. CI runs those three checks, `factory-tests`, the efficiency-bundle
check and security scans on pushes to `main` and pull requests targeting `main` or `develop`.
`stale` and `orphans` remain manual checks; CI exercises their fixtures through `factory-tests`.

Many people run Æion Factory in a plain folder, without git. The link and health checks, the context
fingerprint, the code graph (`tools/architecture/ask`) and the session-start summary then walk the files on disk (skipping `.git`, `.aeion`,
dependencies, caches, the root's build output such as `dist/` or `target/`, and desktop files such as
`.DS_Store`; `.claude/hooks/project_files.py`). Each folder's `.gitignore` applies to it and below for
its simple rules (a name or glob, optionally ending in `/`); negations and paths with a slash are not
read, so what they would hide stays listed. Git counts only when its top level is the project
root: a folder nested in another repository, even a monorepo subfolder that repository tracks, is plain,
and the Stop sign-off reminder, which compares branches, stays silent there. Every harness hook command
falls back from `git rev-parse --show-toplevel` to the current folder. Only `doc-links --diff`, which compares
commits, needs git. A folder whose `.git` git cannot read is a broken repository and fails, as does a
missing comparison base; a valid empty change set remains successful and an unavailable check is
never reported as clean.

Header traceability is extension-independent and bounded; see the discovery scope in
[specs-first](../policies/specs-first.md). The Stop reminder preserves spaces/Unicode in edited
paths and reports an unavailable link check once; unreadable input or a session id shaped like a
path has nothing recorded and passes. The path guard and after-edit also cover MultiEdit and
NotebookEdit (`notebook_path`). `repo-health --json` exposes its source suffix
set and selected file count; its caps are not language-aware lint or security coverage.

Policy hooks require Claude Code 2.1.295+ for `onFailure: block`; the Bash/path guard command timeout is three
seconds (context hooks use five; native adapter hooks use fifteen). Independently, the after-edit hook limits each checker to two seconds for fast feedback.
Nonzero exits, missing executables and timeouts produce exit 2 and at most 15 lines
of diagnostics. Direct script tests do not qualify live harness dispatch or runtime isolation.
After-edit checks require macOS, Linux or WSL: a timed-out check's process group is terminated
before capture pipes are drained, so ordinary descendants do not keep working after the timeout.

The same hook suite tests [bounded intake](../policies/bounded-intake.md), including file/range
thresholds, misleading limiters and preserved native edit/range fields. SessionStart adds two
short intake instructions and the flow mode within its existing 25-line cap.

The flow mode is a per-clone Git setting, read from the repository's local config only
(`git config --local`; includes and the global config do not count). The default team flow works
on `develop`, records a review before each push of it and reaches `main` only through a reviewed
release pull request with green CI. `git config aeion.mode local` sets local play
in the repository's local config: commits stay local, the Stop sign-off reminder is silent, and the safety guards (secrets, Git hook
and force-push bypasses, large dumps) stay on. `git config --unset aeion.mode` restores the team flow.

## Language servers

`tools/claude-plugins/` is a local marketplace with `native-lsp`: TypeScript 7 (`tsc --lsp
--stdio`, the project's own compiler), Deno (`deno lsp`) and Java (Eclipse JDT LS on the project's
JDK, data outside the repository). One server per file extension: enable only those you use.

```bash
claude plugin marketplace add ./tools/claude-plugins --scope project
claude plugin install native-lsp@aeion-local --scope project
```

Check: an `initialize` answer, a definition and references through the `LSP` tool, a deliberate
type error reported then cleared, and the same after a fresh session. Roll back with
`claude plugin uninstall native-lsp@aeion-local --scope project`.

Agent-specific setup and qualification: [compatibility](agent-compatibility.md). Integration pins
require Python 3.12+ excluding 3.14.1. `knowledge-check` also validates public root/setup docs and
the portable efficiency bundle; its bundled Superpowers notice is self-contained.

## Passive pool checks

The seventeen native skills are checked by `tools/skills/lint`: `name` against its folder, a
description of at most 1024 characters that names its trigger, a body of at most 150 lines and no
duplicate name; `tools/skills/tests/test_lint.py` is in `tools/factory-tests`.

`tools/factory-tests` runs `tools/skills/tests/test_pool.py` and the real offline pool check
`python3 tools/skills/pool.py check`. They verify materialized files, support resources, license
restrictions, local-edit preservation and operation without third-party/lifecycle folders.
The root `skills/` data preserves upstream formatting; authored-source size/comment heuristics
exclude this identified pool and report the excluded count. Native code under `tools/skills/`
remains checked. This is not a security-scan exemption. Source refresh is an explicit maintenance
action; normal CI/search/integrity checks need no external source repository.
