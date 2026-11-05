---
type: Runbook
title: "The loops"
description: "Inner, middle and outer loops: the orchestrator's jobs, their models, tools and schedules, and what keeps the outer loop read-only."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - resource: ../../tools/loops/run
    title: "run, which names this doc as its spec"
  - resource: ../../loops/orchestrator.sh
    title: "orchestrator.sh, which runs one job headless"
  - resource: ../../loops/decisions-api/client.sh
    title: "the Decisions API client, off until enabled"
---

# The loops

`loops/orchestrator.sh <job>` runs one job headless (`claude -p`) with its prompt
(`loops/prompts/`), model and thinking level (`loops/model-routing.md`), tool allowlist and
permission mode. It reads only the loop settings of `env.local` (never the Decisions API secret)
and runs nothing while `LOOPS_ENABLED` is not `true`; `--dry-run` prints the settings.
Enabled jobs launch through `tools/context/run`: a verified Graphify/Archify baseline is
recommended (the launcher warns without one), native compaction is fixed at 250k and the checkpoint profile applies. Strict pre-request 300k
admission remains unqualified. See [context safety](context-safety.md) and
[architecture maintenance](architecture-maintenance.md). Dry-run still launches nothing.

| Job | Schedule | Writes |
| --- | --- | --- |
| `outer` | daily | issues only (production through `PROD_READ_COMMAND`, the only allowed production read) |
| `docs` | daily | issues only |
| `security` | weekly and before releases | issues only |
| `middle` | every 30 min on working hours | review comments only |
| `watch` | monthly | a `tech-watch/pending/` package by pull request |
| `retro` | weekly | a pull request of hook rules, skills and preferences |
| `inner --issue N` | on demand or after triage | a branch and a pull request into `develop` for one `agent-ready` issue |

Schedulers: `loops/schedules/crontab.example`, the launchd plist, or
`.github/workflows/outer-loop.yml` (off until the repository variable `OUTER_LOOP_ENABLED` is
`true`). Issues follow `loops/issue-protocol.md`. The Decisions API client
(`loops/decisions-api/client.sh`) refuses to run until `DECISION_API_ENABLED=true`.

## Bounds and read-only jobs

Defaults: `LOOP_MAX_TURNS=30`, `LOOP_TIMEOUT_SECONDS=900`; both must be positive integers.
The deadline, SIGINT and SIGTERM terminate the invocation's ordinary process group. `LOOP_MAX_BUDGET_USD` is an
additional optional API-billing cap, not a replacement for these limits on subscriptions.

Read-only jobs set `AEION_LOOP_READ_ONLY=1`. The shared Bash guard permits fixed checker/Git
read commands, `doc-links --for <path>`, plus issue/review operations, and refuses writer-capable
tools, shell composition and arbitrary Git flags. Their only write is finding/review text under the
ignored `.aeion/loop-bodies/`; `--body-file`/`-F` must name a regular file there as its own
word (an attached `-Fpath` is refused), so an injected
instruction cannot publish another local file. A configured production reader must be an exact, single trusted command;
put complex reads in the approved read-only script rather than interpolating shell pipelines.
Their `gh` takes no `--jq`/`-q`, `--template` or `--repo`/`-R`, so issue text cannot make a loop
print the environment or post to another repository.
Native sandbox/credentials remain separate boundaries; this is not a universal shell sandbox.
No loop deploys, restarts, migrates data or changes a setting: a finding that needs one becomes an
issue for the owner instead.

Every job exports `AEION_LOOP=<job>`, so the path guard keeps its file tools inside the project
(the retro may also read this project's transcripts under `~/.claude/projects/`). The writing jobs
(`inner`, `watch`, `retro`) get the git subcommands their prompts use (`status`, `diff`, `log`,
`show`, `fetch`, `switch`, `checkout`, `add`, `commit`, `push`, `branch`, `rev-parse`), never
`git *`: `git config` and `git -c` could set a key that runs a program on every later git command.
Subcommands alone are not a security boundary: the shared Bash guard also refuses explicit
remote-helper URLs (`<helper>::...`) and transport program overrides (`--upload-pack`,
`--receive-pack`, `--exec`, including abbreviated options). Ordinary HTTPS/SSH remotes remain usable.
The retro writes `knowledge/`, hookify rules (`.claude/hookify.*.local.md`) and `.claude/skills/`,
never the hooks or settings that guard every session; it opens its pull request with `gh pr
create` and reads review comments through `gh pr list`/`view`, without `gh api`.
`inner` still allows any `python3` and `tools/` command, which is a shell in practice; only the
shared guards (secrets, hook and force-push bypasses, git program keys, dumps) and the review/CI
gate bound it.

An enabled inner job reads exact issue labels before launching: absent `agent-ready` refuses;
`severity:high` selects opus/high unless an explicit model/thinking override wins. A maintainer adds
the label, but the issue text stays its author's, so the job also refuses an issue whose
`author_association` is not `OWNER`, `MEMBER` or `COLLABORATOR`. A dry run never
fetches issue metadata and therefore cannot resolve issue severity.

Optional GitHub agent workflows prepare a real architecture baseline before invoking the agent,
use an explicit turn cap and a job deadline, and check out without persisting the token
(`persist-credentials: false`), so the agent's git holds no credential. The outer loop sets
`AEION_LOOP: outer`. They remain disabled until the owner configures them;
their live dispatch/account/plugin behavior is a separate qualification from local loop fixtures.
