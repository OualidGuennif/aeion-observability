# Phase 6 — Constellations: inner, middle and outer loops

> *Organisms form constellations: patterns that repeat on their own schedule, each one small,
> together a system.*

**In one line:** three loops — the session (inner), the branch and pull request (middle), the
scheduled read-only checks (outer) — connected by issues, so problems found at night are fixed
by morning through the same reviewed path as any other change.

> **Agent:** enter plan mode. Find what already runs on a schedule (CI crons, monitors, scripts)
> and what reads production. The outer loop only ever **reads**; propose its read-only path first.

## The three loops

| Loop | Runs | Speed | What it guarantees |
| --- | --- | --- | --- |
| **Inner** | inside a session | seconds | plan → small steps → language-server diagnostics and hooks after each edit → tests → `sign-off` |
| **Middle** | per task | minutes | one branch per task → pull request → `pr-review` (fresh reviewer, one verdict comment) → green CI → merge |
| **Outer** | on a schedule | hours | read-only checks of production, security and docs → findings become issues → an inner loop picks them up |

(The inner/outer vocabulary comes from developer-experience practice: the inner loop is the fast
local edit-build-test cycle, the outer loop the integration, review and release around it.)

### Inner loop

- Plan mode for anything non-trivial (skill `plan`); thin slices (skill `build`); the reflexes of
  Phase 5 on every edit; tests before the claim (skill `test`).
- **Security inside the loop:** a diff that touches authentication, infrastructure, CI or secret
  handling gets `/claude-security` on its changes before the pull request (the `claude-security`
  plugin maps the code, searches it and has separate verifiers try to disprove each finding; only
  survivors are reported). Not on every diff — it costs tokens.
- Ends with the skill `sign-off`.

### Middle loop

- **One branch per task** (`task/<slug>`), small commits, `gh pr create` with what, why and the
  checks run.
- **`pr-review`:** a *fresh* subagent reviews the diff (fresh context catches what the author's
  context hides); every finding is verified before it is reported; one comment goes on the pull
  request:

  ```
  Review: OK            (or)   Review: NOT OK
  - <high|medium|low> path:line -- the finding (at most five)
  Checks: CI <state>; doc-links <result>; tests <what ran>
  ```

- **Merge after `Review: OK` and a green CI**: a task pull request may squash; a release pull request
  (`develop → main`) is merged with a merge commit, never squashed. A change that needs a deploy or a human
  decision (money, risk, data deletion, a policy) waits for that human.
- **Taste:** the skill `pr-taste` reads the owner's pull-request comments and keeps the durable
  ones — architecture, naming, style, security, UI — in `knowledge/policies/owner-preferences.md`,
  one line and a source each; a checkable one becomes a `hookify` rule. The next review applies
  them, so the owner never has to say it twice.
- The same comment becomes the input of the next review: corrections compound.
- Every main update runs the mandatory Graphify/Archify round, including docs-only merges.
  Keep the complete architecture spec current and wait for the exact merged SHA's passing
  analysis before closing work or releasing (`knowledge/operations/architecture-maintenance.md`).

### Outer loop (scheduled, read-only)

A scheduler — **mandatory**, whichever kind you have — runs `loops/orchestrator.sh <job>` headless
(`claude -p`), each job with its own prompt, model, tool allowlist and budget:
The orchestrator uses `tools/context/run`; the project needs a verified initial architecture
baseline and inherits the same context checkpoints as interactive managed runs.

| Job | Default schedule | Reads | Writes |
| --- | --- | --- | --- |
| `outer` health | daily | production through the read-only path (a gateway, a read-only role), CI history | issues |
| `security` | weekly, and before each release | the codebase (`claude-security` scan at medium effort) | issues, a report folder (git-ignored) |
| `docs` | daily | `doc-links`, `knowledge-check`, stale `stale_after` dates | issues |
| `watch` | monthly | the tech-watch method (Phase 3) | a `tech-watch/pending/<date>-<topic>/` package via PR |
| `retro` | weekly | the week's sessions and PR comments (Phase 7) | a PR with lessons, hook rules, skills (`skill-creator`, `hookify`) |

- **Findings become issues**, not fixes: `gh issue create` with labels `loop:outer`,
  `severity:<high|medium|low>`, and `agent-ready` when the fix is clear and small, `needs-owner`
  otherwise (see `loops/issue-protocol.md`).
- **An inner loop picks up `agent-ready` issues** (`loops/orchestrator.sh inner --issue <n>`): one
  issue, one branch, one pull request, the normal middle loop. Nothing reaches the default branch
  without a review comment and a green CI.
- **Safety by construction:** the outer jobs run with a read-only tool allowlist, no secrets in
  their context, a default 30-turn / 900-second budget, and a kill switch (`LOOPS_ENABLED=false`). They never deploy,
  restart, migrate data or change a setting.

### Model routing: `auto`

Every loop defaults to model and thinking level `auto` when no local override exists. The orchestrator
picks by the job's criticality: a small, fast model (e.g. Haiku) for triage and read-only checks;
a balanced one (e.g. Sonnet) for implementation and reviews; the most capable (e.g. Opus) at high
effort for security, architecture and anything labelled `severity:high`. Pin a value to override.

### Schedulers

Pick the one you have; the jobs are the same:

- **GitHub Actions** (`.github/workflows/outer-loop.yml`, off until `OUTER_LOOP_ENABLED` is set):
  `on: schedule`, `anthropics/claude-code-action` with a prompt, or the orchestrator in a runner.
- **A machine that is always on:** `cron` or macOS `launchd` (`loops/schedules/`).
- **Claude's own scheduled tasks or routines**, where available.
- **Per release:** run `security` and `docs` as a release gate.

## Done when

The three loops ran once each for real: a task went branch → PR → review comment → merge; an
outer job opened an issue; an inner run fixed an `agent-ready` issue through a reviewed PR.

## Pitfalls

- An outer loop with write access "just for small fixes": every fix goes through the middle loop.
- Reviews by the author's own context: always a fresh reviewer.
- Scheduling everything daily: the security scan and the watch cost real tokens — weekly and
  monthly are enough.
