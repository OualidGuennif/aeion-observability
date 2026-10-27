---
type: Runbook
title: "Implementation, dashboards and qualification plan"
description: "A staged observe-only pilot, evidence gates for adaptation, concrete dashboard requirements, qualification scenarios and unresolved integration questions."
status: draft
sources:
  - id: spec
    resource: ../components/observability.md
    title: "Framework requirements"
  - id: examples
    resource: ../../examples/README.md
    title: "Synthetic artifacts and worked arithmetic"
---

# Implementation plan

## Current state

The research and offline paired-cohort/fixture guards remain available without services.
An explicitly requested [local pilot](../../demo/README.md) now implements a Deno/Hono
workload, a host-native Python supervisor/cockpit, Flue + Pi coding agents whose tools run in
OpenShell, OpenTelemetry, Langfuse, Hindsight and claude-mem. Its [separate specification](../components/docker-demo.md) defines the limited
measurement boundary and context/handover controls. Local evidence is recorded in
[validation](../../work/validation.md); it does not establish all scenarios below.
Factory, CROA and OPS sibling files are unchanged.

The following is a delivery plan, not a report of passing runtime qualification. Each phase
has a specific exit gate; do not jump directly from dashboards to automatic model switching.

## Phase 0 — define the measurement boundary

Select one coding harness/version, one local sandbox profile and one task family. Keep both
subscription and API paths in the compatibility plan, but qualify them independently. Select
the deliverable stage, privacy policy, outcome channel and accounting basis.

Deliver:

- A task/acceptance contract and a small representative corpus with a held-out subset.
- A mapping of native telemetry fields to the proposed contract, including known gaps.
- One approved baseline profile and a named owner for outcome labels and corrective work.
- A source/version/capability snapshot, limits, paid-test budget if used, and capture policy.
- A threat/boundary review: telemetry ingest, secrets, evaluator and control-plane separation.

Exit: the team can explain every metric's denominator and who can falsify each evidence source.
Missing OPS enforcement remains an explicit pilot limitation; do not claim governed actuation.

## Phase 1 — observe and verify one real task

Use native metadata telemetry first. Configure one Collector with explicit producer identity,
redaction/allowlisting and bounded export. Send traces to the chosen backend and resource
metrics/logs to the existing APM, with shared opaque run identity.

Start with Langfuse core as the trace/evaluation candidate only if its self-hosted footprint
fits. If an existing backend already satisfies the required queries, reuse it. Do not deploy
Langfuse, Phoenix, OpenLIT and a second metrics stack simultaneously for comparison.

Add a protected usage/outcome ledger and an immutable artifact/check reference. In a single-user
observe-only pilot, a bounded local export can be enough to inspect events; concurrent admission
later needs transactional storage. Never expose provider reconciliation credentials to agents.

Exit: a task report reconstructs the session, check result, human dependence and cost basis.
Test failure/partial cases too; one successful trace screenshot does not qualify the pipeline.

## Phase 2 — make data trustworthy enough to compare

Run the accounting, privacy, identity, outcome and outage scenarios below. Establish visible
coverage metrics and observed collection overhead. Compare native events to provider/adapter
evidence where available. Check retry ownership and the difference between caller and serving model.

Exit: declared mappings and data-quality gates pass, with uncertainty and gaps represented
correctly. Required privacy/identity/accounting failures block automated optimization.

## Phase 3 — evaluate a small profile catalog offline

Compare baseline, a cheaper or lower-effort bundle, and a stronger recovery bundle only where
each adds a real hypothesis. Use clean isolated workspaces, identical resources/toolchain where
appropriate, randomized task order and an untouched holdout. Include compute, judge, setup,
cache and failed-attempt costs.

Exit: a candidate report demonstrates task-level quality/time/cost evidence and failed cases.
Insufficient sample size is an acceptable result. Do not select a winner from request latency
alone or transfer a public leaderboard ranking into an Æion quality guarantee.

## Phase 4 — shadow the controller

Implement deterministic eligibility and recommendation recording. Resolve all credentials via
references outside the workload. Keep application disabled. Replay recorded decisions from
frozen policy/feature snapshots and inspect exclusions and unsupported-control cases.

Exit: deterministic decisions reproduce; latency overhead is acceptable; permission, budget,
privacy and state-migration gates cannot be overridden by workload input.

## Phase 5 — bounded task-level canary

Only after its evidence and authorization exist, apply the candidate to a limited low-impact
cohort with a fixed control. Initially hold one model/profile per task; preserve the frozen
fallback strategy. Log propensities and pending-label exposure. Have a tested external kill
switch and a compatible rollback target.

Exit: pre-registered non-inferiority/improvement gates, data coverage, all-in cost and delayed
regression checks hold. A profile can be rejected or remain in shadow without blocking useful
observe-only functionality.

## Phase 6 — add adaptation only where it wins

Introduce one checkpoint escalation or a task-level contextual policy, not both at once. Compare
against the fixed baseline and an equally simple rule. Account for cold context, restart,
evaluation, selection overhead and exploration. Requalify after material upstream changes.

Exit: incremental benefit exceeds the stated complexity/cost threshold without reducing safety,
coverage or verified autonomy. Otherwise retain the simpler policy.

## Dashboard requirements

Dashboards are read models over canonical events/ledgers. An existing APM can render them; no
custom frontend is required for v0. Each chart shows cohort, time window, count, policy/profile
version, accounting basis, maturity and evidence coverage.

| View | Required measures | Decision it supports |
| --- | --- | --- |
| Task overview | Offered/started/accepted/assisted/failed/pending counts and quality bounds | Are we completing useful work? |
| Triangle / Pareto | All-in cost per autonomous success vs p95 task time, quality/uncertainty encoded | Which profiles remain feasible? |
| Session timeline | Interactions, model attempts, tools, waits, checks and controller decisions | Where did this task go wrong? |
| Time decomposition | Setup, inference, tool/CI, human/governance wait and restart | Which bottleneck is worth changing? |
| Cost ledger | Known/reconciled/estimated/allocated amounts, unresolved exposure, retries and fees | Are savings real and complete? |
| Autonomy and repair | Human-help categories/minutes, acceptance and delayed regressions | Did fewer prompts hide extra repair? |
| Model/provider matrix | Qualified capability, request failures, task outcomes, counts and revisions | Is the problem endpoint health or task quality? |
| Reasoning/output/cache | Effort bundles, truncation, task success, retained-prefix reuse and total spend | Which inference setting helps this workload? |
| Tools/environment | Failure classes, repeated calls, resource limits, dependency/setup latency | Is model switching the wrong remedy? |
| Controller | Mode, decision overhead, stale features, excluded arms, switches and rollback | Is optimization itself behaving correctly? |
| Experiment | Assignment counts, propensities, pending labels, intervals and subgroup results | Is promotion justified? |
| Telemetry health | Drops, orphan joins, duplicates, queue/disk usage, outcome/usage coverage | Can any chart be trusted? |

Example analytical queries, expressed as requirements rather than invented product APIs:

- Join offered tasks to their latest outcome version; retain tasks without a matching outcome.
- Sum each task's latest canonical charge observations; keep estimates/allocations separate.
- Group mature comparable tasks by whole-policy treatment, not only the final serving model.
- Calculate cost per autonomous success from total cohort cost, including failed tasks.
- Drill from a metric exemplar to a bounded trace, task artifact and check evidence reference.

## Qualification scenarios

All cases are **planned, not executed**. Use synthetic canaries before any real user-content test.
Record exact versions/configuration and evidence for each applicable result.

| ID | Scenario | Required result |
| --- | --- | --- |
| Q01 | One task, several interactions and a resumed run | Stable task lineage, distinct run identity, no rebilling old calls |
| Q02 | Parallel tools/subagent work | Causal links; resource work differs correctly from elapsed time |
| Q03 | Claude cache categories vs OpenAI-style prompt totals | Correct input normalization with no subset double counting |
| Q04 | Duplicate span/log/Broadcast for one request | One charge entity with multiple provenance observations |
| Q05 | Two separately billed retries | Both charges retained, despite one logical call |
| Q06 | Cumulative stream usage frames and a final total | Replace cumulative reports; do not sum them |
| Q07 | Stream interrupted before usage | Unknown quantity/charge; bounded reconciliation, held exposure |
| Q08 | Late reconciliation or refund delivered twice | Idempotent version update and correct current totals |
| Q09 | Native cost in credits, USD and subscription allocation | Explicit units/conversion; no unexplained sum |
| Q10 | Provider fails before/after headers, 429/5xx and auth errors | Bounded appropriate retry; no auth/permission bypass |
| Q11 | Required unsupported parameter or empty eligible endpoint set | Refuse profile; never drop required control silently |
| Q12 | Tool/schema/context compatibility under real round trips | Preserve IDs/state; reject incomplete/invalid action arguments |
| Q13 | Model switch with pending tool or opaque continuation state | Block unsafe migration; safe checkpoint/restart path |
| Q14 | Cached prefix after effort/model/provider change | Correct measured reuse/cost; no assumed cache portability |
| Q15 | CPU/RAM/disk/PID exhaustion during tests | Infrastructure cause recorded; resource ceiling preserved |
| Q16 | Human corrects patch in another session | Original task marked assisted and repair linked |
| Q17 | Required review with no corrections | Governance effort visible without false rescue classification |
| Q18 | No human feedback or missing intervention channel | Unknown autonomy, not inferred success |
| Q19 | Agent claims success after modifying checker/tests | Protected verification rejects invalid acceptance evidence |
| Q20 | Later regression after provisional acceptance | Versioned outcome revision and honest mature-cohort statistics |
| Q21 | Secret/prompt/code canaries in attributes, bodies and errors | No default export; approved diagnostic tier handled separately |
| Q22 | Workload forges producer/task/outcome identity | Rejected or retained only as untrusted claim |
| Q23 | Payload/rate/cardinality attack | Bounded impact; visible rejects/drops; no controller authority change |
| Q24 | Collector/backend outage, disk full and abrupt restart | Bounded queues, loss/coverage evidence and tested recovery |
| Q25 | Sampled-out trace with paid request/task completion | Accounting/outcome denominators remain complete |
| Q26 | Two concurrent requests at shared budget boundary | Atomic reservation admits only permitted exposure |
| Q27 | Crash after reservation, uncertain dispatch or cancel | No double settlement or premature release of unknown exposure |
| Q28 | Stale/poisoned health or LLM-injected policy suggestion | No unauthorized profile/setting; freshness gate enforced |
| Q29 | Canary quality regression or retired rollback model | Stop candidate; compatible rollback or safe checkpoint |
| Q30 | Outcome label backlog / uneven missingness | Pending exposure capped; no fabricated labels or biased promotion |
| Q31 | Repeated checks of experiment results | Pre-registered/sequential inference respected |
| Q32 | Changed model, CLI, SDK, prices or mapping schema | Detect drift, expire affected qualification and re-evaluate |

## Explicit unresolved questions

| Question | Evidence needed before relying on it |
| --- | --- |
| Which exact native CLI version exports the required spans/events? | Installed version plus sanitized actual capture |
| Which Claude subscription/token flows are supported for the selected unattended use? | Current official eligibility/auth documentation and scoped operational test; SDK use not inferred |
| How much per-attempt detail survives native CLI retries? | Fixture and controlled errors compared to mediated requests |
| Do cost/cache/reasoning fields survive each Anthropic-compatible route? | Captured protocol fixtures and normalization checks |
| Which DeepInfra model values/tiers/cache controls are actually honored? | Exact model capability, request/reply evidence and behavior tests |
| Can missing DeepInfra usage/cost be reconciled per request? | Documented/account-authorized interface or explicit unresolved limit |
| Are OpenRouter provider/usage/Broadcast joins complete for this destination? | Account/interface test, IDs, permissions, delay and retention limits |
| Does selected Langfuse v4 ingestion preserve required attributes/types? | Pinned release, exported fixture and query/UI checks |
| Is the local backend footprint worth operating? | Pilot memory/disk/latency/maintenance measurements |
| Do alternative profiles reduce actual repair and total cost? | Representative mature controlled cohort, uncertainty and all-in ledger |
| Does the intended OPS boundary meet the controller's trust assumptions? | Implemented effective controls and qualification evidence |
| Does a CROA-scoped audit require additional evidence? | Separate kit assessment for the declared system, boundary and period |

## Factory integration deliverable

Keep this project separate. A future Factory-callable integration accepts a frozen task/run
manifest and outputs a bounded task report plus advisory policy recommendation. It uses
existing Factory spec/check/review evidence; it must not mutate the caller's permissions,
provider secrets, global hooks or delivery gates.

Map CRAFTED to measurable evidence: context contract (C), source/tool inspection (R), bound
spec/check versions (A), procedure versions (F), executed checks (T), reviewed artifact (E),
and recorded outcome/decision evidence (D). Measure useful completion rather than counting
rituals such as lines changed, hooks fired or agents spawned.
[Factory CRAFTED](https://github.com/OualidGuennif/aeion-factory/blob/main/efficiency/CRAFTED.md)

## Completion record for this research

The source register records inspected documentation/papers and reading depth. The worked
examples are synthetic and contain no credentials or real session content. Knowledge/link
checks and example arithmetic can validate this dossier's consistency; they do not qualify
the planned runtime scenarios above. Record actual validation results in the final handoff.
