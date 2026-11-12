---
type: Component
title: "Æion Factory architecture"
description: "Complete source-backed specification of Æion Factory's authority, execution, Knowledge, context checkpoints, analysis and delivery."
status: stable
generated:
  by: aeion-factory/1.6.2
  at: 2026-11-09
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
  - resource: ../../demo/factory/api.py
    title: "Authenticated factory selection and current admission"
  - resource: ../../demo/factory/dispatch.py
    title: "Deterministic feature lifecycle"
  - resource: ../../demo/factory/product_checks.py
    title: "External product verification boundary"
  - resource: ../../demo/factory/publication.py
    title: "Credential-separated protected publication"
  - resource: ../../demo/factory/review_context.py
    title: "Operator-only old-envelope reassessment"
---

# Æion Factory architecture

## Intent

Æion Factory is a Git repository template and local toolset for agent-assisted engineering. The
owner authorizes scope and delivery. Agents plan and edit; Python/Git checks establish bounded
structural facts; fresh review establishes the verdict; GitHub records PR/merge/CI evidence.
There is no application server, broker, production database or deployed Æion Factory control plane.
Adopting projects keep their existing instructions and architecture.

### This adopting repository

This repository adds an opt-in host-native cockpit and a local Docker telemetry stack to that
development foundation. Its implemented engine lives in `demo/factory/`; the Flue/Pi harness in
`demo/flue/src/` runs product workers through OpenShell tier3. The authenticated cockpit admits
ordered catalog MDs, freezes task identity/scopes, reserves the existing daily budget and records
durable stages. Current native qualification is rechecked before admission and role execution.
Under Factory 3.0, the runtime integrates OpenShell 0.1.8 with bridge read/stat caching, Flue 2.3.0
persistent state for author execution and passed-check finish steering, Hindsight 1.2.1 SDK with
cognitive synthesis fallback, and Langfuse v5.2 enterprise prompt management and multi-dimensional
evaluation scores. The [execution contract](factory-flue.md) owns these runtime facts; the
[cockpit contract](operator-cockpit.md) owns selection and presentation.

Workers propose candidate files without host credentials, mounts, a Docker socket or unrestricted
egress. The supervisor packages production code before candidate tests, gives tests another
workspace, and grades the product in separate application/verifier processes. Two eligible
reviewer model families must differ from each other and from author/preparer families. Separate
publisher/release subprocesses open the product PR, verify exact-head CI and confirm main.
A required check that finished without success does not merge: it queues a bounded correction
with the check names, one fixed repair sentence for a known check, and the agents' notes.
An unreadable or pending check stays held. Three identical protected-check failures stop the
author as `repeated_check_failure` and the next attempt receives those test names. A passed
gate is not described with the author's earlier self-check, including an older attempt. A builder-error receipt keeps the execution diagnostics and the protected-check evidence. The catalog
shows the admission expiry and does not renew it.
A CLI stop while the author was still working resumes that same build and model; the execution
contract states the evidence, the three-resume cap, and which stops still start another model.
A security proof inside its last hour is refreshed before a sandbox opens; a failed refresh
holds that same build and does not start another attempt.
Only integration of the current contract unlocks dependent MDs; a generated patch or old-contract
success does not. The product has its own GitHub repository and credentials. Observer mirrors
are not product workspaces. Fixed PostgreSQL migration/restore oracles, a separate unit-test
database and frozen React build/Vitest tools belong to that supervisor boundary. Ordinary workers
cannot modify them or the maintainer-only CI update program. PostgreSQL/React product delivery and a demo require their own actual
checks and deployment receipts; capability qualification alone never claims them complete.

Review envelope v2 binds a diff from the exact frozen Git base alongside complete candidate
files, the MD and protected acceptance. One explicit operator command can reassess an old
full-files-only rejection when base/task/artifact and known usage remain unchanged, with no
prior publication. The state transaction archives that rejection and increments its generation;
the shared judgment path reruns external gates and two fresh reviewer families, including the
original rejecting reviewer. It grants no worker/HTTP retry authority, approval or author charge.
A v2 hold caused only by reviewer failures (a missing typed verdict, never a rejection) allows
one further operator retry flag with fresh gates and votes; a second failure stays held.

Langfuse receives bounded role, request, tool and failure metadata via the privacy-filtering
collector. The local ledger and verified artifacts retain authority independently of dashboard
availability. Hindsight recall and local checkpoints are advisory. Model routing compares persisted measured
outcomes within matching contract, runtime, treatment and execution-bound cohorts, with explicit cold-start
priors. A candidate that edits a code file whose Spec document is outside the feature's write scopes is refused before publication and instructed to revert that file; protected unit-test failures carry bounded JUnit XML diagnostics, track full failure signatures across a five-check streak after baseline reproduction, advance through correction rounds on `repeated_check_failure`, and seed the cleanest validated candidate on a relaunch of the same base and spec. The maintained architecture view names these boundaries and source anchors; the workflow
and lifecycle views additionally retain the foundation's reviewed delivery and context controls.

Claude Code retains its native hooks. Codex, OpenCode, Pi, dsh (DeepSeek Harness), Devin, Droid
(factory.ai), Google Antigravity and Grok load the same instructions and skills, with narrow adapters to
the existing secret guards, edit checks and handover checkpoints (Devin and Antigravity have no
compaction checkpoint; Droid, which reports no tokens, owes its closure after a compaction; Grok
cannot refuse compaction). Grok's hooks live in `.grok/`. During closure, plain read commands (`cat`, `head`, `sed -n`, `rg` and
the like, without operators, globs or secret files) are closure tools, because Codex reads only
through its shell. Droid owns `.factory/`, so
Æion Factory's local state lives in the ignored `.aeion/`. A per-clone flow mode selects local mode, the default
(local commits, no sign-off reminder), or the team flow (`aeion.mode team`: develop, review, release PR);
the safety guards run in both.
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
| Connector checks | Byte equality against a checkout or a git reference, config wiring, regular-file and executable-mode checks, steer identity and role | `tools/agents/adapter-check`; `connectors.py` (one file list), `refs.py` (one reference reader and git mode) |
| Project update | Move an adopted project between factory references: connectors byte for byte, other factory files three-way, never the application's `VERSION` | `tools/agents/template-update`; baseline from `--from-ref`, `.aeion-factory` or an exact tag inference; names `AGENTS.md`, merged settings, conflicts and `knowledge/` for a human with proposals; refuses dirty trees and linked destinations |
| Desktop install | Pin the dsh profile's plugin at a release instead of a working tree | `tools/agents/dsh-install`; `<profile>/aeion-factory` symlink |
| Hook adapter | Read event JSON and call a bounded local check | stdin/stdout JSON; failure blocks where supported |
| Headless Pi RPC | Keep one `pi --mode rpc` process alive through the settlement compaction and its resumed run, streaming the answer and failing closed on a failed compaction or the deadline | `tools/agents/pi-rpc`, reached through `tools/agents/run pi rpc`; the factory extension supplies the guards |
| dsh connector | Guard every tool call and drive the 250k/300k handover-compact-resume cycle | `.dsh/plugins/factory/*.js`; the root compaction service (headless) or the `/compact` command on idle (web, whose service is isolated in an agent-preset group) |
| Context budget | Usage, closure-only state, checkpoint receipt (with per-file digests, so a stale one names what changed), 300k forced compaction | `.aeion/context/<session>.json`; per-session file lock |
| Handover | Recovery facts for the current session | Ignored `work/handovers/<session>.md`, created atomically only when closure needs it |
| Knowledge/link/health checkers | Frontmatter, caps, traceability and diff coverage | Exit code + bounded diagnostics; no provider |
| Optional loops | Select prompt/model/tools and run a managed headless task | Off unless enabled; outer loop reads production only through its configured read path; `AEION_LOOP` keeps file tools in the project, writing jobs get named git subcommands only, inner needs a maintainer-written issue |
| Analysis wrapper | Freeze Git, Graphify, evidence validation and Archify finalization | Ignored `.aeion/analysis/<sha>/` and immutable receipts |
| GitHub workflows | PR checks and post-main analysis; artifact retention | Read-only checkout/job permissions; no generated-source push |
| Native language servers | Editor diagnostics for their registered language | Local processes; explicit plugin enablement |
| Demo playground | An agent builds a real app on a git-less copy of the factory and files feedback for the base | `demo/plan/` briefs; per harness a tracked journal and `feedback_for_aeion/`, an ignored `workspace/` copy |
| Product verification boundary | Isolated compile/test/acceptance running outside candidate control with disposable PostgreSQL and external Node/browser verifiers | `demo/factory/product_checks.py`; passes explicit instructions for feature contracts, Quarkus test lifecycle hooks and database role safety |

Normal task: read -> approved plan -> component spec -> thin changes/tests -> docs/current task
update -> fresh review -> authorized PR merge -> exact-merged-SHA analysis -> closure/release.
Deployment remains the adopting project's own guarded procedure. Æion Factory loops never deploy.

### Context and recovery

In the Claude profile, native auto-compaction is enabled at 250k. The state machine starts RUNNING; observing 250k
latches HANDOVER_REQUIRED and emits one alert to user and agent. Code/subtask tools are refused;
closure docs and fixed check commands remain. A checkpoint validates handover sections, Knowledge,
doc links, repository health and current task updates, then hashes source and handover bytes.
Any later source or handover change invalidates readiness. An observed size back under 250k ends the
latch, because a harness that compacts without the adapter seeing its compact SessionStart (dsh does)
would otherwise stay gated at a fraction of the threshold; the closure it owed survives as
`closure_owed`, which the settlement enforces. That debt never re-latches a later fall: a session that
climbs over 250k again and compacts again is still under the threshold, so it is released again (Stop
keeps the debt), never gated until the gate becomes permanent. A latch a harness set because its own
compaction resumed it in closure (Codex, Droid) is marked `resumed_in_closure` and stays latched until
the handover verifies. A verified receipt releases the gate: it owes
exactly one handover, and a compaction the plugin cannot guarantee must never hold a session hostage, so
the checkpoint command stays admitted whatever session token it carries (`ready` opens the gate, never the
spelling). PreCompact refuses an absent checkpoint, and a stale one whose handover is incomplete; when a
complete handover was verified and the tree moved since, it compacts and leaves the closure owed
(`closure_owed`) instead, because the gate admits only the checkpoint command that could refresh the
receipt. The native `PreCompact` in `tools/agents/hook.py` applies the same exception to dsh and
OpenCode, with OpenCode starting its own epoch because it sends no compact SessionStart. Pi reaches that
hook only for its own window compaction (`native`), which a refusal would cancel, so it compacts
regardless and owes the handover and checkpoint in the new epoch, as Codex and Droid do. At 300k the
compaction runs too and leaves the closure owed, because code is already frozen
there. A compact SessionStart begins RECOVERING
and supplies the handover pointer; new positive native usage permits RUNNING. Resume alone does not clear STOPPED. The 250k and 300k alerts
name the checkpoint command; a settlement that still owes closure names the missing receipt; closure
admits a project's own Markdown docs, never code. The suggested base is an existing ref
(`origin/develop`, `origin/main`, else `HEAD`), and a refused checkpoint reports the failing check's
bounded output. Because dsh compaction is not dependable in every profile, its start context and
gate messages also name the recovery: after the handover, `work/current.md` and the checkpoint
verify, stop the session and resume from the handover instead of working past 250k.

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
requires a recorded review of the exact commit; CI runs for `main`, `develop` and pull requests, architecture for `main`: on the
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
its pre-compaction receipt is consumed per attempt; a fresh receipt was live-confirmed at 272k on 2026-11-02. Pi's extension maps `tool_call`,
`tool_result`, `before_agent_start` and `session_before_compact` to the same guards and cancels a
compaction without a verified handover; its 250k compaction runs at settlement in interactive and
RPC runs, and a one-shot headless run now stops cleanly with the verified handover (1.9.2; see
agent-compatibility). Loop cancellation terminates the ordinary
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

The materializer applies the security patches in `tools/skills/patches.json` (the
skill-creator eval viewer and the instinct import), then three reviewed comment-only SAST
annotations from `tools/skills/annotations.json`, each bound to an exact original file hash. Source
changes require renewed review. Original/materialized hashes are both retained;
search and checking remain offline and no source execution or broad scan exemption is added.
