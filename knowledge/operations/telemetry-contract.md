---
type: Runbook
title: "Session telemetry and accounting contract"
description: "Proposed identities, event schemas, timing boundaries, token normalization, accounting lineage, metric labels and data-quality rules."
status: draft
sources:
  - id: upstream
    resource: ../references/sources.md
    title: "Pinned standards and official integration sources"
  - id: fixtures
    resource: ../../examples/validate_fixtures.py
    title: "Offline synthetic-fixture consistency gate"
---

# Session telemetry contract

The `aeion.*` fields and `aeion.observability.*` versions below are proposed local contracts.
They are not an existing OTel standard or implemented SDK. JSON examples are synthetic design
fixtures, not captures of a user's sessions.

## Offline fixture validation

`python3 examples/validate_fixtures.py` checks the five bundled JSON files and the session
JSONL example. It rejects duplicate object keys and non-finite numbers, verifies synthetic-only
observe/shadow guards, and checks policy/profile, task/run, artifact/check and charge links.
Identical deliveries with the same producer/boot/event identity count once; conflicting
duplicates fail. Each demonstrated inference attempt has one complete USD charge after
reconciliation, and their sum must match the outcome's inference-only amount.

This is a consistency gate for these examples, not a production schema, privacy sanitizer,
general charge reconciler or proof that any recorded assertion actually occurred. It neither
calls a provider nor qualifies the runtime scenarios described below.

## 1. Identity and causal structure

| Identity | Meaning | Lifetime |
| --- | --- | --- |
| `task_id` | One accepted work objective and acceptance contract | Survives retries, resumed runs and human repair |
| `run_id` | One bounded execution attempt of that task | New after a clean restart; retains `task_id` |
| `harness_session_id` | Actual vendor/harness conversation identity | Native value or null; may span several tasks/runs |
| `interaction_id` | A user/controller-to-agent interaction | One response/tool loop as bounded by harness |
| `logical_call_id` | Intended inference operation in the agent loop | Shared by its observable retries |
| `attempt_id` | An actual observable provider request attempt | Unique for each potentially billable attempt |
| `provider_request_id` | Returned provider identifier | Native value and issuing system; null if absent |
| `router_generation_id` | OpenRouter generation identifier, where returned | Distinct from upstream provider request ID |
| `tool_call_id` | One requested tool operation | Linked to actual execution/effect evidence |
| `decision_id` | One controller decision at a named boundary | Linked to requested and acknowledged actuation |
| `artifact_digest` | Immutable output tree/patch/package identity | Used by tests, review and outcome records |

Record `parent_run_id`, parent agent IDs, fork/replay origin and task dependency links only when
known. An offline replay gets new IDs and `environment=evaluation`; it must not enter live
production counts. Resuming a conversation does not justify rebilling old requests.

Use one trace per interaction or bounded run segment; link long tasks with `task_id`, `run_id`
and OTel span links. Do not hold a root span open for days and expect every backend's retention,
tail sampling or UI to handle it. The authoritative task lifecycle lives outside sampled traces.

Trace shape, when available:

```text
run / interaction
  decision.select_profile
  inference.logical_call
    inference.attempt A
    inference.attempt B (retry, if actually observed)
  tool.call
    permission.wait
    tool.execution
  validation.check (trusted checker or separately linked CI trace)
```

Do not fabricate attempt spans from an aggregate retry count. Retain the count and mark
attempt-level visibility partial. A provider may retry internally without exposing every attempt.

## 2. Event envelope

Required: `schema_version`, `event_id`, `event_type`, `occurred_at`, `observed_at`, `task_id`,
`run_id`, `producer`, `data`. Optional IDs are null or omitted under the documented schema.

| Field | Proposed rule |
| --- | --- |
| `schema_version` | `aeion.observability.event/v0-draft` for these examples |
| `event_id` | Unique within producer identity and boot; stable across delivery retries |
| `occurred_at` / `observed_at` | UTC event time / collector receipt time; clock uncertainty retained |
| `producer` | ID, component kind, version and boot ID; authenticated identity assigned by ingestion |
| `sequence` | Native per-process sequence if exposed; never infer contiguous capture without its contract |
| `trace_id`, `span_id` | Valid W3C IDs when present; no secret or business text encoded into them |
| `data` | Event-specific, typed and allowlisted; no arbitrary object copied from a tool/provider |
| `evidence_quality` | `observed`, `provider_reported`, `estimated`, `derived`, or `unknown`, per relevant field |

The collector sets the trusted source classification using authenticated transport and launch
bindings. A workload-provided `trust=trusted` string has no authority. Unknown event versions
are bounded/quarantined and counted; they do not silently mutate the controller's feature schema.

Proposed initial limits: 64 KiB per metadata event, bounded strings/arrays, finite numbers,
no duplicate JSON keys, no control-character log injection, and per-producer rate/byte limits.
These are starting design limits, to be sized with fixtures, not upstream limits or measured capacity.

## 3. Event families and authoritative producers

| Family | Minimum data | Preferred producer |
| --- | --- | --- |
| `task.offered` / `task.classified` | Contract/cohort versions, family, boundary, risk/data class | Trusted intake, before assignment |
| `run.started` / `run.ended` | Revisions, policy/profile IDs, resources, reason, incomplete work | Launcher/supervisor |
| `interaction.started` / `interaction.ended` | Session link, turn index, duration and terminal reason | Native harness |
| `routing.decided` | Features snapshot, eligible/excluded profiles, selected profile, reason, propensity | Controller |
| `routing.applied` / `routing.failed` | Decision ID, adapter acknowledgement, request correlation | Inference adapter |
| `inference.started` / `inference.completed` | Route/model/parameter provenance, timings, finish/error class, attempt visibility | Adapter plus harness/provider observations |
| `usage.observed` / `usage.reconciled` | Native usage, amount/unit/basis, completeness, charge identity and revision | Provider adapter/reconciler |
| `tool.requested` / `tool.completed` | Bounded tool class, call ID, duration, status; optional effect evidence reference | Harness; effect verified by owning service |
| `context.compacted` / `context.prepared` | Input/output token estimates, context-strategy/version, manifest digest and lost-context status | Harness where observable; estimates labelled |
| `retrieval.completed` / `memory.accessed` | Strategy/index/memory version, bounded result count, latency and scope | Instrumented retrieval/memory layer; content omitted |
| `agent.delegated` / `agent.handoff` | Parent/child run links, role/profile, allowed boundary and terminal result | Harness/supervisor, where delegation actually occurs |
| `capability.decided` | Control ID, allow/deny, policy digest and sanitized target class | OPS boundary |
| `resource.sample` / `resource.limit` | CPU/RAM/disk/PID envelope, exhaustion reason and interval | Supervisor/runtime |
| `human.intervention` | Kind, corrective/non-corrective, effort, reason and coverage source | Human/workflow channel |
| `artifact.exported` / `validation.completed` | Digest, check version, result, integrity and evidence refs | Exporter/trusted checker |
| `task.outcome_recorded` / `task.outcome_revised` | Acceptance dimensions, maturity, intervention coverage, supersession | Outcome evaluator |
| `telemetry.health` / `telemetry.gap` | Producer heartbeat, queue/drop counters, coverage and freshness | Collector/supervisor |
| `cleanup.completed` / `cleanup.failed` | Remaining resources/access and lifecycle evidence | OPS supervisor |

Events record claims at different stages. A requested tool call is not its execution, an
authorized action is not its effect, and an exported patch is not an accepted task outcome.

## 4. Model and parameter provenance

Keep separate fields for:

- Harness and version; wire protocol (`anthropic_messages`, `chat_completions`, other qualified path).
- Authentication mode (`claude_subscription`, `provider_api`, other explicit modes).
- Requested model/alias and resolved model revision, where resolution is observed.
- Model publisher, router (`openrouter`, direct), requested provider constraint and observed serving endpoint.
- Requested parameter bundle, source (`explicit`, harness default, provider default unknown), and observed acknowledgement.
- Requested/effective service tier, context-window limit, tool schema version and adapter version.

An HTTP 200 does not prove a parameter was honored. Model metadata is advertised capability;
qualification establishes interoperability. If effective sampling/serving details are not returned,
keep them unknown. Never infer publisher or serving provider from a protocol compatibility string.

Version the requested context manifest as well: Factory instructions, selected skill/procedure,
MCP/tool catalog, retrieval/index/memory and compaction strategy. A file's presence in the repo
does not prove the harness read it. Record observed loads only when exposed, with the capture
gap explicit. This lets an experiment distinguish a model change from a changed harness/context.

For OTel export, use the pinned conventions for `gen_ai.operation.name`, `gen_ai.provider.name`,
`gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.request.reasoning.level`, timing and
usage. Retain separate Æion route fields if native instrumentation identifies the client-facing
provider/protocol rather than the actual serving endpoint.
[Pinned client-inference contract](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/client-inference.md)

## 5. Timing: name the boundary before plotting a percentile

| Measure | Boundary | Interpretation |
| --- | --- | --- |
| Task wall time | Intake to declared deliverable completion | Includes admission/setup/agent/tool/wait/restart time |
| Time to verified acceptance | Intake to verification/acceptance | Includes evaluator delay; report separately from execution time |
| Request end-to-end | Client dispatch to terminal response/error | May include client retries; label scope |
| TTFT | Dispatch to first generated-token observation | May include reasoning; keep producer definition |
| First visible content | Dispatch to first visible text/content | Distinct from headers, keepalives and reasoning |
| First useful action | Dispatch to a valid complete tool call/action | Often more relevant to coding than first text |
| Generation duration | First to last observed generated token | Only when timestamps/count scope is known |
| Tool wait / execution | Permission or queue interval / running interval | A faster model cannot remove a slow test suite |
| Setup/cold start | Task admission to harness-ready | Includes image/environment readiness where measured |
| Human/governance wait | Explicit waiting intervals and reason | Separate corrective rescue from required approval |
| Decision overhead | Decision start to adapter-ready | Includes feature/classifier cost and policy lookup |

Use monotonic clocks for local durations; wall clocks for cross-system joins with an uncertainty
bound. If domains cannot be synchronized, preserve independent durations and causal links.
Queue time inside a hosted provider remains unknown unless explicitly returned.

Do not treat SSE chunks as tokens. Average inter-token delay is `(last-first)/(tokens-1)` only
when tokens and timestamps cover the same population and at least two tokens exist. Non-streaming
completion time is not measured TTFT. Provider-side throughput and client-visible throughput
remain differently scoped observations.

For parallel tools/subagents, sums of span durations exceed wall time. Use unions of intervals
and critical-path analysis; report resource work separately. Never average per-worker p95s to
obtain a task p95. Split successful, failed, timed-out and cancelled task durations visibly.

## 6. Token normalization

Preserve the native object in a bounded **allowlisted usage-only** representation with source
and adapter mapping version. Native unknown fields must not become automatic telemetry exports.

| Path | Input normalization | Output normalization |
| --- | --- | --- |
| Claude Code's documented Anthropic categories | `input_tokens + cache_read_tokens + cache_creation_tokens` | Native output; reasoning subset only when actually exposed |
| OpenRouter Chat Completions | Native `usage.prompt_tokens`; cache details retained as documented subdivisions | Native `usage.completion_tokens`; reasoning detail is a subdivision |
| DeepInfra Chat Completions | Native `usage.prompt_tokens`; cache reads/writes retained under matching documented model behavior | Native completion count; no invented separate reasoning count |
| Anthropic-compatible gateway | Qualify gateway response and harness interpretation together | Do not assume Chat Completions fields survive translation |

Claude's cache-mapping rule is explicitly documented in its monitoring page. DeepInfra shows
cache-read/write details inside prompt usage; OpenRouter documents native token usage and
reasoning/cache details. [Claude mapping](https://code.claude.com/docs/en/monitoring-usage#map-input-tokens-to-opentelemetry-genai-semantic-conventions),
[OpenRouter usage](https://openrouter.ai/docs/cookbook/administration/usage-accounting),
[DeepInfra retained-cache usage](https://docs.deepinfra.com/chat/prompt-cache-retention)

Proposed normalized fields: `input_tokens_total`, `output_tokens_total`, `cache_read_input_tokens`,
`cache_write_input_tokens`, `reasoning_output_tokens`, each nullable with a provenance label.
Cache TTL subcategories partition a cache-write aggregate when documented; do not add both.
Do not add cache/reasoning subsets to their parent totals a second time.

At the pinned OTel revision, inference usage counters and per-operation histograms have different
purposes. Select the matched instruments from the adapter's versioned mapping; do not build
accounting by summing token histogram bucket/count values.
[Pinned inference token metrics](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/gen-ai-token-metrics.md)

An interrupted stream lacking final usage is incomplete, even if some text arrived. A missing
cache/reasoning field is unknown, not necessarily zero. Preserve whether a provider explicitly
reported zero. Different models tokenize the same source differently; token counts alone are
not a fair cross-model measure of work or quality.

Validate finite nonnegative counts, declared subset relationships and known cumulative/delta
semantics. If a provider reports contradictory quantities, preserve a bounded native observation
and mark normalization invalid/unknown. Do not silently clamp values or repair them into a
plausible but invented bill. A documented provider exception needs its own tested mapping.

## 7. Accounting ledger

One charge entity has multiple observations, not multiple additive charges:

```text
charge identity -> provisional usage -> provider-returned amount -> reconciled amount
                                            -> correction/refund (versioned)
```

Required charge fields: `charge_id`, `attempt_id` where known, router/provider request identity,
payee/account namespace, amount as a decimal string, native unit/currency, normalized currency
and conversion evidence if used, cost basis, completeness, observation ID and supersession.

| Cost basis | Meaning | Aggregation rule |
| --- | --- | --- |
| `provider_returned` | Amount returned for this call/charge | Provisional until reconciliation scope is known |
| `provider_reconciled` | Matched to provider accounting/export for a declared period | Supersedes the matching earlier observation |
| `estimated` | Native quantities times a versioned price schedule | Keep separate from reported/reconciled totals |
| `subscription_allocated` | Chosen allocation of a fixed subscription | Report allocation method; not per-call invoice |
| `unknown` | Charge or quantity unresolved | Preserve exposure/reservation and reconciliation deadline |

Rules:

1. Deduplicate deliveries with `(authenticated producer, event_id)`. Join multiple instruments
   to a charge identity; do not bill the same request once from its span and again from its log.
2. A distinct paid retry is a distinct charge. A logical-call ID alone is not a billing key.
3. Prefer provider request IDs plus account scope. With absent IDs and uncertain cardinality,
   mark the join unresolved rather than deduplicate by prompt text or timestamp proximity.
4. Cumulative stream usage replaces prior cumulative observations; delta-only streams sum
   only under a tested provider mapping. Never sum all cumulative frames.
5. Reconciliation updates the charge version and derived totals idempotently. Retain provenance;
   a refund does not make the original observation disappear.
6. Use decimal money. Record price units, effective time, context-tier rates, cache write/read,
   reasoning inclusion, service-tier premium, request/tool fees, discounts and currency treatment.
7. OpenRouter API usage describes cost in credits; Broadcast documents USD costs. Preserve the
   interface's unit and use an explicit checked conversion contract before combining them.
8. For prepaid routing, do not add upstream reference cost on top of the router's inclusive
   charge. For BYOK, keep router fees and actual provider invoices separate; reference inference
   amounts are not automatically actual invoices.
9. Include test/evaluator model calls, sandbox/compute and observability costs. Separate gross
   consumption from incremental cash expense when infrastructure is already paid for.
10. Return `known_amount`, `estimated_amount`, `unresolved_charge_count` and exposure range;
    do not label a partial known sum as a complete total.

Count background compaction, helper/delegated agents, embeddings and evaluation requests where
they consume resources. Use per-charge records as the additive layer; session/SDK totals may
already include child calls. Keep unresolved attribution in an explicit unallocated bucket so
every known account charge remains visible without guessing which task caused it.

OpenRouter supports generation-ID usage lookup. Availability, permissions, propagation delay
and retention must be tested; poll with a bounded retry/dead-letter policy. No equivalent
DeepInfra per-generation reconciliation interface was established by this study.
[OpenRouter generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation)

## 8. Metrics and labels

Proposed bounded labels: environment, task family, risk/data class, policy generation,
approved profile ID, harness family, router, bounded provider/model catalog entry, outcome/error
class and evidence-quality class. Bound active policy/model revisions and retire stale series.

Keep task/session/request/user/repository IDs, raw paths, URLs, arbitrary tool names, prompt
hashes and digests in protected traces/events, not metric labels. Use exemplars for drill-down.
Opaque IDs are still sensitive metadata. Do not propagate user identity in public trace headers.

| Signal group | Useful measures |
| --- | --- |
| Demand and outcomes | Offered/started tasks, mature accepted autonomous outcomes, assisted outcomes, rejected/abandoned/pending tasks |
| Time | Task and acceptance p50/p95, deadline misses, setup/tool/permission/decision distributions |
| Cost | All-in known/estimated cost, unresolved exposure, cost per verified autonomous success |
| Behavior | Retry/tool-error/truncation rates, verified milestone progress, compaction count and restart cost |
| Quality | Autonomous acceptance, corrective minutes, delayed regression, check and intervention coverage |
| Policy | Profile assignments, fallback reasons, switch rate, canary exposure, rollback count |
| Telemetry health | Export errors/drops/queue/disk, late events, orphan spans, usage/outcome join coverage and feature age |

Outcome revisions must not decrement monotonic counters silently. Compute current cohort quality
from versioned outcome records, or publish mature terminal counts plus explicit correction metrics.
Diagnostic trace sampling is separate from complete task/outcome/accounting retention.

Coverage denominators come from a qualified independent request/task boundary. Without that
boundary, “100% observed” means only “100% of records we received,” not complete capture.
