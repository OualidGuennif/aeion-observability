---
type: Reference
title: "State of the art: observable and adaptive agent sessions"
description: "Primary-source review of telemetry standards, coding harnesses, observability backends, gateways and task-aware routing research, checked 2026-10-23."
status: draft
sources:
  - id: register
    resource: sources.md
    title: "Source register and reading depth"
---

# State of the art — 2026-10-23

## Finding and recommendation

The useful framework is a combination of **portable telemetry, independently checked task
outcomes, and a bounded execution controller**. Standard trace backends already solve much of
the inspection/evaluation problem. Provider routers already solve some price/health routing.
Neither gives an Æion-specific guarantee of successful coding without human repair.

Recommend **OTel Collector + a versioned task/outcome/usage contract + Langfuse core as the
first evaluation-backend candidate + existing OPS enforcement**. Start with explicit rules
and a few approved profiles. Test a contextual policy only after collecting valid labels.
Keep backends replaceable and the controller independent of dashboard availability.

This is an engineering synthesis. It is not an upstream product, a claim that every project
has been surveyed, or evidence that this combination already improves Æion performance.

## 1. Standards: transport is mature; GenAI meaning still moves

OTLP is the interchange layer. The GenAI semantic conventions are explicitly **Development**
and now live in their own repository. This study pins commit
`9ffc7e00c639be7712e544e3e54331e885dccf84`. It includes inference, agent, workflow and tool
signals. Pin the normalization map; preserve native fields and test migrations rather than
calling all `gen_ai.*` fields stable. [GenAI specification](https://github.com/open-telemetry/semantic-conventions-genai/tree/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai)

The pinned inference conventions distinguish requested/response model and reasoning level.
Their token counters treat cache input and reasoning output as subsets of respective totals.
Do not copy old tutorials that combine obsolete metric names with current attribute names.
[Client inference](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/client-inference.md),
[token metrics](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/gen-ai-token-metrics.md)

OpenInference supplies OTel instrumentation and its own AI attributes. It is useful with Phoenix
and other compatible backends, but OTLP compatibility alone does not establish identical token,
session or observation-type semantics. Use an explicit mapping rather than parallel duplicate
instrumentation. [OpenInference](https://github.com/Arize-ai/openinference)

**Implication:** Æion needs a small semantic contract above OTel, not another telemetry protocol.
Keep task lineage, intervention, verification and policy decisions in `aeion.*` fields, with
defined producers and evidence quality. Use native upstream names only where their semantics match.

## 2. Coding sessions: observe the harness and the environment

Claude Code exports OTel metrics/events and optional beta traces. Trace spans can connect
interactions, LLM calls and tool execution, including permission waits. Native token categories
need normalization, and its monetary counters are estimates. Content flags and metric identity
labels require an explicit privacy/cardinality policy. A native instrumentation path is the
first candidate; qualify the exact version rather than assuming a transcript exporter is needed.
[Claude Code monitoring](https://code.claude.com/docs/en/monitoring-usage)

Langfuse's Claude integration also documents a Stop-hook transcript path. That path is useful
for retrospective inspection, but the documented script exports conversation/tool content and
uses SDK internals. It is not a request-time controller or a complete mediation boundary.
Do not install it unchanged as Æion's default capture path.
[Integration and limitations](https://langfuse.com/integrations/developer-tools/claude-code)

The Claude Agent SDK exposes a model-changing method, while the CLI documents model/effort
selection. Those are actuation surfaces to qualify; they do not prove arbitrary per-request
control through every gateway or subscription authentication mode. API adapters and stock CLI
execution remain different profiles. [Python SDK](https://code.claude.com/docs/en/agent-sdk/python),
[CLI model configuration](https://code.claude.com/docs/en/model-config)

OpenAI's current agent-evaluation guidance connects traces, graders and repeatable datasets.
This supports workflow evaluation; it does not supply a cross-provider, externally enforced
Æion controller. [Agent evaluations](https://developers.openai.com/api/docs/guides/agent-evals)

**Implication:** collect three perspectives: harness behavior, trusted runtime/resource
observations, and actual delivered outcomes. Do not use a provider trace as evidence of a
tool's external effect or an agent transcript as evidence of a sandbox's confinement.

## 3. Backends and routing components

The table describes documented capabilities, not a local installation or comparative benchmark.
Feature availability and licenses must be checked again for the release selected for a pilot.

| Candidate | Useful capabilities | Boundary/trade-off | Æion position |
| --- | --- | --- | --- |
| [Langfuse](https://langfuse.com/docs/evaluation/overview) | Traces, scores, annotation, datasets, experiments and CI evaluation | Core MIT; governance additions have separate terms; self-hosting is a multi-component stack | First trace/evaluation candidate |
| [Phoenix](https://github.com/Arize-ai/phoenix) | Local/self-hosted tracing, datasets, evaluation and experiments | Repository uses ELv2 with a hosted/managed-service restriction; do not describe it as unrestricted permissive OSS | Useful evaluation alternative, license scope considered |
| [OpenLIT](https://github.com/openlit/openlit) | OTel-oriented agent/LLM observation, evaluation and infrastructure visibility | Apache-2.0 project; verify needed integration depth and operational footprint | Alternative when unified OTel operations matter more |
| [MLflow](https://www.mlflow.org/docs/latest/llms/tracing/index.html) | OTel tracing, experiments and GenAI evaluation in an existing ML workflow | Apache-2.0 repository; some documented advanced features require Databricks | Reuse if already operated |
| [New Relic](https://docs.newrelic.com/docs/ai-monitoring/intro-to-ai-monitoring/) | Existing APM, feedback, token/cost inspection and alerts | Hosted platform; AI UI support depends on actual instrumentation and models | Good existing APM destination; do not rebuild it |
| [LiteLLM Router](https://docs.litellm.ai/docs/routing) | Endpoint routing, health/limits, latency/cost strategies and affinity | Core MIT with enterprise exceptions; extra proxy and translation surface | Optional if a real gateway need emerges |
| [vLLM Semantic Router](https://vllm-sr.ai/docs/overview/semantic-router-overview/) | Explicit signals, decisions, eligible models and routing algorithms; local/cloud backends | Apache-2.0; Envoy/control-plane/classifier complexity; protocol matrix needs testing | Strong reference, later reuse candidate |
| [OpenRouter routing](https://openrouter.ai/docs/guides/routing/provider-selection) | Multi-provider price/health/performance preferences and constraints | Managed routing; task correctness is outside its observation | Reuse provider routing inside the allowed set |
| [DeepInfra API](https://docs.deepinfra.com/chat/overview) | Direct model selection, inference controls, service tiers and fail-fast queue behavior where supported | Model-dependent support and incomplete compatibility; no demonstrated task-outcome optimizer here | Direct controlled API path |

Source-license evidence: [Langfuse](https://github.com/langfuse/langfuse/blob/main/LICENSE),
[Phoenix](https://github.com/Arize-ai/phoenix/blob/main/LICENSE),
[MLflow](https://github.com/mlflow/mlflow/blob/master/LICENSE.txt),
[LiteLLM](https://github.com/BerriAI/litellm/blob/main/LICENSE),
[Semantic Router](https://github.com/vllm-project/semantic-router/blob/main/LICENSE).
These upstream licenses do not become Æion's license merely because the tools are compared here.

### Why Langfuse is a candidate, not a mandatory platform

Its OTLP endpoint accepts traces and maps several GenAI/OpenInference conventions. That is not
an instruction to send logs/metrics to the same endpoint. Self-hosting includes web/worker,
Postgres, Redis/Valkey, ClickHouse and blob storage. The operational cost belongs in the triangle.
[OTel ingestion](https://langfuse.com/integrations/native/opentelemetry),
[self-hosting architecture](https://langfuse.com/self-hosting)

Current documentation is v4. The migration guide announces removal of legacy Cloud API
endpoints on **2026-11-16**. Build against the current supported interfaces and test the actual
self-hosted release. Do not start from an old v3 ingestion/query tutorial.
[Migration guide](https://langfuse.com/faq/all/deprecated-api-migration)

Halo is an analysis/resource-management assistant with approval-scoped actions. It can help
investigate data; it is not evidence of a qualified autonomous runtime optimizer.
[Halo documentation](https://langfuse.com/docs/halo)

### Gateway observation is incomplete session observation

OpenRouter Broadcast can export provider-request traces to external backends, with per-destination
privacy mode. It runs after requests complete. It can complement native harness data but cannot
observe local checks, human repair or unmediated tools. Prevent duplicate accounting when a
request appears in Broadcast, the SDK and harness telemetry.
[Broadcast](https://openrouter.ai/docs/guides/features/broadcast)

Two commercial routes may reach the same underlying serving provider. An OpenRouter route
served by DeepInfra and a direct DeepInfra route are not necessarily independent outage domains.
Use observed serving lineage where available; otherwise mark that dependency unknown.

New Relic supports native OTLP ingestion. Mapping custom agent spans into a particular AI UI
still needs a fixture-based check. A successful OTLP POST does not prove a useful session view.
[New Relic OTLP](https://docs.newrelic.com/docs/opentelemetry/best-practices/opentelemetry-otlp/)

Modal documents export of audit/function logs and resource/input-event metrics. That is a good
example of joining compute lifecycle to application evidence; it does not give an API client
visibility into a remote model provider's GPU scheduler.
[Modal OTel integration](https://modal.com/docs/guide/otel-integration)

## 4. Routing research: what transfers and what does not

| Work | Verified mechanism / evidence scope | Useful lesson | Transfer limit |
| --- | --- | --- | --- |
| [FrugalGPT, Chen, Zaharia, Zou](https://arxiv.org/abs/2305.05176) | Prompt adaptation and learned LLM cascades; task benchmarks | Escalate only where verification justifies the extra call | Cheap-first plus a judge can add latency/cost; coding trajectories differ |
| [RouteLLM, Ong et al.](https://arxiv.org/abs/2406.18665v4) | Strong/weak routing learned from preference data; benchmark evaluation | Learn a request's relative model value rather than use price alone | Preference is not independently verified coding success; calibrate on Æion tasks |
| [RouterBench, Hu et al.](https://arxiv.org/abs/2403.12031v2) | Reusable outcomes for comparing multi-LLM routing | Compare against fixed models and random mixtures on common data | Primarily request-level data; cannot replay changed tool/environment trajectories |
| [Online selection, Poon et al.](https://arxiv.org/abs/2506.17670) | LinUCB-style selection under evolving prompts; myopic-regret formulation | Contextual bandits can learn from limited sequential feedback | A myopic guarantee is not a long-horizon task-quality guarantee |
| [SWE-Router](https://arxiv.org/abs/2607.00053) | Partial cheap-model trajectory informs continue/escalate decision | Early execution reveals difficulty hidden from an issue prompt | The stronger route starts from the original prompt in the described design; account for restart cost |
| [ORACLE, Raj et al., v4](https://arxiv.org/html/2607.22465v4) | Task/model/verifier binding, delayed feedback and concurrency-aware dispatch | Separate dispatch from slow verification; match verifier to task family | Local vLLM scheduling experiments/replays do not expose equivalent controls on hosted APIs |
| [WISERouter, Li, Gao, Lakshmanan](https://arxiv.org/html/2607.23765v1) | Contextual bandits with workload budget and paid exploration | Include data collection in the optimization budget | Assumes independent/stationary contexts within its horizon; studies monetary constraint, not this whole triangle |
| [AgentRouter, Paul, Nandy](https://arxiv.org/abs/2609.22951) | Reported step classifier using trajectory features | A step's difficulty may differ within one task | Abstract-level review only here; reported gains and implementation not reproduced |

The newer papers are research evidence, not certified production building blocks. No savings
percentage from them is adopted as an Æion forecast. The recent arXiv version of ORACLE has a
different title from older TRACE-Router indexing; cite the inspected version, not the stale title.

### Deeper reading of the two closest systems

ORACLE's v4 implementation binds a program at its first request and reuses that model/verifier.
Its appendix distinguishes measured scheduling runs from frontier replays over precomputed
per-task outcomes. Its DISC reservation concerns locally observable KV capacity, not a hosted
provider's dollar budget. Borrow delayed terminal feedback and coherent task binding; do not
claim DISC can govern OpenRouter/DeepInfra queues without additional evidence.
[Methods and appendices](https://arxiv.org/html/2607.22465v4)

WISERouter explicitly discusses stationary independent contexts, a finite workload horizon and
feedback acquisition. It reports only monetary constraints on two datasets. Dependent coding
steps, delayed acceptance, drifting providers and unknown final bills violate shortcuts one
might otherwise import from its formulation. Use it as a research direction once task-level
labels and a trusted spending boundary exist. [Limitations and Appendix A](https://arxiv.org/html/2607.23765v1)

### Why a bandit is not v0

At low volume, there may be too little evidence per task family/profile. Exploration is paid,
labels arrive late, and failed tasks can be more expensive to judge. Model revisions and context
strategies change the treatment. A deterministic baseline plus a small randomized canary is
easier to audit and often more informative than a large learned policy.

For later off-policy evaluation, log actual assignment probabilities and overlap. Doubly robust
methods combine outcome and logging-policy information; they cannot reconstruct outcomes for
never-tried actions without assumptions. [Dudík, Langford, Li](https://arxiv.org/abs/1103.4601v2)

Repeatedly peeking at ordinary fixed-sample intervals invalidates their intended interpretation.
Pre-register a fixed comparison or use a suitable sequential method with its assumptions.
[Howard, Ramdas, McAuliffe, Sekhon](https://arxiv.org/abs/1810.08240v9)

## 5. Quality is an outcome contract, not a transcript sentiment

Agent evaluation guidance distinguishes the final environmental outcome from what the agent
says happened, and recommends multiple grader types. For coding, begin with independent
checks and artifact inspection; use calibrated model judgments only for residual subjective
requirements. [Anthropic agent evaluations](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)

Infrastructure can change both failure rates and attainable results in coding evaluations.
Freeze/report CPU, memory, deadline, sandbox, toolchain and concurrency; do not attribute every
OOM, dependency outage or slow test to model capability.
[Infrastructure noise study](https://www.anthropic.com/research/infrastructure-noise)

Æion's quality target therefore needs acceptance plus intervention coverage and a delayed
regression window. An agent that hides problems, never asks, edits tests, or submits early must
not appear better than one that correctly requests a necessary clarification.

## 6. What the first pilot should answer

1. Can we correlate a real CLI session, resource lifecycle and immutable checked patch?
2. Do native tokens/attempts/costs survive each protocol path without double counting?
3. Is the dominant delay inference, tool execution, setup, queueing, or governance waiting?
4. Which few model/effort bundles preserve autonomous acceptance on representative tasks?
5. Does switching beat a fixed profile after retries, cold caches, restarts and evaluator costs?
6. Does any measured improvement survive uncertainty, stratification and delayed failures?

The [implementation plan](../operations/implementation-plan.md) turns these into executable
qualification work. Hardware/platform performance, live API compatibility and Æion savings
remain unknown until that work is performed.
