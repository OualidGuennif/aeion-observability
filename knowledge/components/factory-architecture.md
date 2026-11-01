---
type: Component
title: "Æion Factory architecture"
description: "Complete source-backed specification of Æion Factory's authority, execution, Knowledge, context checkpoints, analysis and delivery."
status: stable
generated:
  by: aeion-factory/1.6.2
  at: 2026-10-29
sources:
  - id: instructions
    resource: ../../AGENTS.md
    title: "Authority and task flow"
  - id: budget
    resource: ../../tools/context/budget.py
    title: "Context checkpoint state machine"
  - id: refresh
    resource: ../../tools/architecture/refresh
    title: "Analysis snapshots and provenance"
  - id: graph
    resource: ../../tools/architecture/graph.py
    title: "Native structural Graphify extraction"
  - id: workflow
    resource: ../../.github/workflows/architecture-refresh.yml
    title: "PR and main maintenance rounds"
  - id: views
    resource: ../../tools/architecture/views.json
    title: "Reviewed Archify views and evidence anchors"
---

# Æion Factory architecture

## Intent

Æion Factory is a Git repository template and local toolset for agent-assisted engineering. The
owner authorizes scope and delivery. Agents plan and edit; Python/Git checks establish bounded
structural facts; fresh review establishes the verdict; GitHub records PR/merge/CI evidence.
There is no application server, broker, production database or deployed Æion Factory control plane.
Adopting projects keep their existing instructions and architecture.

Claude Code retains its native hooks. Codex, OpenCode, Pi, dsh (DeepSeek Harness), Devin, Droid
(factory.ai) and Google Antigravity load the same instructions and skills, with narrow adapters to
the existing secret guards, edit checks and handover checkpoints (Devin and Antigravity have no
compaction checkpoint; Droid, which reports no tokens, owes its closure after a compaction). During closure, plain read commands (`cat`, `head`, `sed -n`, `rg` and
the like, without operators, globs or secret files) are closure tools, because Codex reads only
through its shell. Droid owns `.factory/`, so
Æion Factory's local state lives in the ignored `.aeion/`. A per-clone flow mode selects the team flow (PR, review, CI)
or local play (commits on main, no sign-off reminder); the safety guards run in both.
Their native token/compaction interfaces differ; compatibility is not a claim of identical
enforcement. See [agent compatibility](../operations/agent-compatibility.md).

### Vocabulary and authority

Knowledge is canonical policy/specification; OKF is the maintained concept/frontmatter/link
discipline. Skills describe task procedures. Hooks are event-triggered feedback/control within
the supported harness. A checkpoint preserves an unfinished task; a baseline records source
analysis at a commit. Neither replaces owner authorization, tests or canonical documentation.

Agents keep reasoning private and omit optional progress narration, including JSON notes.
Necessary user decisions and final validation remain visible. [Token feedback](../policies/bounded-intake.md)
is advisory; it does not enforce the model's private reasoning format or a token-saving guarantee.

## Data sources

| Source | Content / owner | Freshness |
| --- | --- | --- |
| `AGENTS.md` and owner instruction | Self-check and stop-and-ask triggers, precedence, boundaries (secrets, untrusted input), task workflow / owner | Read at task start; dated pointers to `CHANGELOG.md` and `work/current.md` |
| `knowledge/` | Policies, components, ADRs, operations and references / reviewed repository | Owning fact updated with its code |
| `work/current.md` | Open task state / current worker | Every meaningful sign-off/checkpoint |
| Git objects and diff | Immutable source and changed/deleted paths / Git | Explicit target/base SHA |
| Current session transcript | Latest native input/cache/output token counts / Claude Code | Bounded tail at each control event |
| Graphify/Archify | Structural relations, rendered views and check receipts / pinned tools | Per target commit; derived, never policy |

## Inputs

Task input is the owner's approved scope plus relevant instructions and component specs.
Untrusted issues/pages/model output cannot grant permissions. Existing path/Bash guards cover
their documented accidental-read/command patterns; they are not complete sandbox isolation.

Context events have a validated session ID, event kind, tool input where applicable and that
session's transcript path. Counts are nonnegative native integers; cache categories count once.
The bootstrap admits one first prompt; unavailable subsequent usage refuses further work.
An asynchronous transcript delay blocks the current action without permanently stopping the
session; a later valid observation can recover. Invalid complete records and the observed hard
limit remain terminal. Every event, including PreCompact, latches a warning crossing.
Subagent tool events key state by parent plus `agent_id` and read the child's own transcript.
Unavailable child usage stops that child's profile without contaminating the parent's state.

Analysis takes an explicit target commit, optional comparison base and reviewed integration/view
manifests. A diverged PR uses the effective merge base while preserving its exact requested
base and target SHAs in the receipt. Main pushes retain their ordinary ancestor comparison.
Only allowed tracked text enters extraction. Secret paths (one list for the guards, analysis and
the context fingerprint, `.claude/hooks/secret_names.py`) refuse analysis, symlinks
are excluded, and unsupported formats remain explicitly inventory-only. Tool versions are pinned.
The graph includes code and native Markdown structure/frontmatter/links; semantic inference by
an LLM is outside the baseline. Each doc's frontmatter `sources`, read from disk, adds a `specifies` edge to
the file it names (Graphify alone links only code names written in a body); `coverage.json` lists any
`resource` that names no file in the corpus. `refresh` runs only on a root that is its own git
repository; a plain folder nested in another one is refused before any git call. This keeps the default independent of model credentials.
`graph.py` also adds `specified_by` edges from `Spec:` lines, `names_file` edges from tests that name a
file, and exact `imports` from `deno info` in a Deno project. For day-to-day questions on the working
tree, [`tools/architecture/ask`](graph-queries.md) keeps its own graph in `.aeion/graph/`, apart from the baselines.
Setup stamps Graphify's commit archive URL and SHA-256, including replacement of a same-version wheel
from another source; analysis refuses mismatched package provenance or a dirty Archify checkout.

## Outputs

### Components and execution

| Unit | Responsibility | Interfaces / persistence |
| --- | --- | --- |
| Instructions and seven-phase guide | Owner precedence, scope and adoption | Markdown links; `CLAUDE.md` points to `AGENTS.md` |
| Skills | Plan/spec/build/test/review/sign-off/ship, template update and focused procedures | `.claude/skills/*/SKILL.md`; no second task ledger |
| Connector checks | Byte equality against a checkout or a git reference, config wiring, steer identity | `tools/agents/adapter-check`; `connectors.py` (one file list), `refs.py` (one reference reader) |
| Project update | Move an adopted project to a release, writing only the files a harness loads | `tools/agents/template-update`; names `AGENTS.md`, merged settings and `knowledge/` for a human |
| Desktop install | Pin the dsh profile's plugin at a release instead of a working tree | `tools/agents/dsh-install`; `<profile>/aeion-factory` symlink |
| Hook adapter | Read event JSON and call a bounded local check | stdin/stdout JSON; failure blocks where supported |
| Context budget | Usage, closure-only state, checkpoint receipt (with per-file digests, so a stale one names what changed), 300k forced compaction | `.aeion/context/<session>.json`; per-session file lock |
| Handover | Recovery facts for the current session | Ignored `work/handovers/<session>.md`, created atomically only when closure needs it |
| Knowledge/link/health checkers | Frontmatter, caps, traceability and diff coverage | Exit code + bounded diagnostics; no provider |
| Optional loops | Select prompt/model/tools and run a managed headless task | Off unless enabled; outer loop reads production only through its configured read path |
| Analysis wrapper | Freeze Git, Graphify, evidence validation and Archify finalization | Ignored `.aeion/analysis/<sha>/` and immutable receipts |
| GitHub workflows | PR checks and post-main analysis; artifact retention | Read-only checkout/job permissions; no generated-source push |
| Native language servers | Editor diagnostics for their registered language | Local processes; explicit plugin enablement |
| Demo playground | An agent builds a real app on a git-less copy of the factory and files feedback for the base | `demo/plan/` briefs; per harness a tracked journal and `feedback_for_aeion/`, an ignored `workspace/` copy |

Normal task: read -> approved plan -> component spec -> thin changes/tests -> docs/current task
update -> fresh review -> authorized PR merge -> exact-merged-SHA analysis -> closure/release.
Deployment remains the adopting project's own guarded procedure. Æion Factory loops never deploy.

### Context and recovery

In the Claude profile, native auto-compaction is enabled at 250k. The state machine starts RUNNING; observing 250k
latches HANDOVER_REQUIRED and emits one alert to user and agent. Code/subtask tools are refused;
closure docs and fixed check commands remain. A checkpoint validates handover sections, Knowledge,
doc links, repository health and current task updates, then hashes source and handover bytes.
Any later source or handover change invalidates readiness. PreCompact refuses an absent/stale
checkpoint, except at 300k, where the compaction runs and leaves the closure owed (`closure_owed`)
until a verified receipt, because code is already frozen there. A compact SessionStart begins RECOVERING
and supplies the handover pointer; new positive native usage permits RUNNING. Resume alone does not clear STOPPED. The 250k and 300k alerts
name the checkpoint command; a settlement that still owes closure names the missing receipt; closure
admits a project's own Markdown docs, never code. The suggested base is an existing ref
(`origin/develop`, `origin/main`, else `HEAD`), and a refused checkpoint reports the failing check's
bounded output.

Observed usage at 300k or invalid complete usage latches STOPPED. Unavailable usage after bootstrap
blocks the current action and can recover after a valid observation. A PreCompact refusal uses
that event's blocking decision. No extra model turn
is requested to finish missing docs. A partial task remains incomplete. The current harness is
qualified only as a checkpoint profile: it has no proved before-every-request bound or exact
mid-response cutoff. Strict launch is refused; Codex/OpenCode token enforcement remains unqualified.

Before tools run, the shared path/Bash guards also refuse recognizable large dumps under the
[bounded-intake policy](../policies/bounded-intake.md). Native range/result fields and edit kinds
are preserved. This reduces accidental intake without rewriting tool output or adding a runtime.

### Knowledge, state and retention

Canonical facts exist once in Knowledge with sources and `Spec:` pointers. Frontmatter/tags
retain existing formats and limits. Generated graphs/views are navigation aids; inferred links
retain confidence labels and cannot create canonical facts. `work/current.md` retains only open
tasks. Completed task state is removed; durable choices go to ADRs/policies and commit history.
Local handovers are concise, contain no transcripts/secrets, and can be removed after completed
task recovery/closure. State deletion is a manual recovery decision, not an automatic stop bypass.

Analysis output and caches stay ignored locally. CI artifacts retain the workflow's configured
retention period (14 days); a missing/expired baseline must be rebuilt. There is no mutable
latest pointer, graph database, shared writable cache or exactly-once delivery assumption.

### Trust and failure behavior

Scripts never execute model-produced commands. Only fixed closure commands and validated Git
arguments pass to subprocesses. Tool installations are project-local and pinned; normal analysis
requires no LLM credential; agents ask before installing them. CI uses a read-only token and
never sends source to a model. A local
agent/runtime still needs its existing account. Raw CLI sessions outside the managed launcher
and deliberately modified local hooks are outside the enforcement claim.

Each analysis builds a clean immutable snapshot. File hashes, source anchors, native coverage
and Archify's schema/provenance/browser gates must pass before publication. Missing tools,
browser, refs, evidence anchors, extraction coverage or output fail the round. Jobs run separately
per target; duplicates use a valid same-SHA receipt only after artifact verification. A newer
failed round leaves older SHA artifacts intact but stale. Bounded subprocess timeouts terminate
the invocation; no background service/retry queue continues it. CI reruns retry the same target.
Each requested comparison has a separate receipt bound to the baseline receipt hash; reusing
the graph never substitutes an earlier base or changed-path set for the current comparison.

### Delivery and rollback

Pre-commit/CI retain Knowledge, doc-link, health and security gates; CI also fails when the
efficiency bundle drifts from its sources. Daily work lands on `develop`, whose pre-push hook
requires a recorded review of the exact commit; CI runs for `main` and pull requests, architecture for `main`: on the
release PR `develop → main` (merged with a merge commit, then tagged `vX.Y.Z`)
and every main push, including docs-only and multi-commit pushes, records changed/removed paths,
and uploads immutable outputs. It cannot undo a merge: a failed round prevents release and
completed-work claims until corrected. A local baseline is recommended before managed execution
and installed only on the user's yes; launchers warn without one.
Rendering uses its permanent SHA directory; an atomic final receipt publishes success only
after every gate passes. Moving Archify HTML would invalidate its native path provenance.

Rollback is a reviewed normal Git revert, followed by checks and a fresh analysis for that
revert SHA. Never force-push main or reuse an older graph as if it describes the reverted tree.
No production migration, rollback command or availability/SLO is applicable to this template.

## Invariants

1. Owner/repository instructions and canonical Knowledge remain authoritative (review and
   existing Knowledge/link checks).
2. 249,999/250,000 and 299,999/300,000 observations have explicit boundaries; stopped state is
   not reset by resume; unavailable usage is refused (`tools/context/tests/test_budget.py`).
3. Compaction readiness binds the handover and exact source state; later edits invalidate it
   (`test_budget.py`, checkpoint/compaction tests). At the alert the checkpoint is admitted only when
   its path resolves to this root's `budget.py`, from any working directory.
4. Source evidence belongs to the target SHA; missing/ambiguous anchors, secret paths and nodes
   outside Archify's one-to-three sources fail
   (`tools/architecture/tests/test_refresh.py` and real Archify gates).
5. Required code/Markdown extraction is complete structurally; deletions cannot survive in a
   freshly assembled current graph (coverage checks and the real baseline).
6. A PASS receipt names its SHA and artifact hashes; tampered/missing output is never reused
   (`test_refresh.py`, corruption and missing artifact tests).

## Determinism

Source enumeration, hashing, native structural extraction, state transitions and schema checks
are deterministic within pinned tools. Rendering/browser evidence depends on the browser/runtime
and records its receipts. Spec/diagram meaning is reviewed engineering judgment. Neither tests
nor schema checks prove complete semantic understanding. No throughput/latency/token-saving
measurement or live 250k/300k guarantee is asserted. No extra agents are required for execution;
the existing fresh PR reviewer remains.

## Acceptance checks

Run the commands in [build and test](../operations/build-and-test.md), plus the two context and
architecture test scripts, setup, and `tools/architecture/refresh --target HEAD --base <sha>`.
The baseline must include code/docs coverage, source-backed overview/delivery/context views and
passing Archify browser receipts. Inspect the initial views visually before claiming readability.
After merge, inspect the analysis job for that exact main SHA. Native long-session qualification
remains unavailable until a real controlled run succeeds; a failed or partial run is not a pass.

## Out of scope

Production infrastructure, a hosted documentation service, LLM-generated canonical specs,
semantic completeness guarantees, universal harness support, a strict token ceiling without
runtime admission control, and automatically enabling additional agents or Superpowers bootstrap.

Native adapters validate line endings and required path/command fields before guard dispatch.
OpenCode uses the V2 directory id/setup entrypoint and native prompt/tool/compaction callbacks;
its pre-compaction receipt is consumed per attempt. Pi's extension maps `tool_call`,
`tool_result`, `before_agent_start` and `session_before_compact` to the same guards and cancels a
compaction without a verified handover. Loop cancellation terminates the ordinary
child process group as well as enforcing deadlines. No SDK dependency is bundled for the plugin.

## Versioned skill library

The root `skills/` directory is a passive, self-contained source library: 525 physical
skill folders, 99 physical agent profiles, support files, copied licenses and a provenance
catalog. These are not symlinks into another repository. Reading, searching and checking
work in a Factory-only checkout. `tools/skills/pool.py` manages materialization and integrity;
only a refresh needs the four allowed source copies. The optional external lifecycle folder
contains the human/LLM maintenance brief only and is never a runtime dependency.

The 16 native task skills remain under `.claude/skills`; `skill-route` is the single added
native selector, shared through `.agents/skills`. Native rules take precedence over pooled
methods. Profile files never launch agents or choose models by themselves. See
[skill selection](../operations/skill-selection.md) for authority and licensing boundaries.

The materializer applies three reviewed comment-only SAST annotations from
`tools/skills/annotations.json`, each bound to an exact original file hash. Source
changes require renewed review. Original/materialized hashes are both retained;
search and checking remain offline and no source execution or broad scan exemption is added.
