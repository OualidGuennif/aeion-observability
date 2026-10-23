---
type: Reference
title: "Primary-source register and evidence scope"
description: "Dated documentation, source, license and paper references behind the framework, with explicit reading depth and unverified implementation claims."
status: draft
---

# Source register — checked 2026-10-23

Only primary documentation, upstream source/license files and original papers support the
technical synthesis. Secondary search results were used for discovery, then checked against
primary material. This is a curated survey, not an exhaustive scan of the internet.

**Evidence levels:** documentation establishes an advertised API/feature; source establishes
the inspected code/license; a paper establishes what its authors report under its assumptions.
None establishes local integration, deployed controls or reproducible Æion performance.

The [retrieval fingerprints](source-snapshots.json) record successful read-only source fetches,
resolved URLs, bytes and SHA-256 values. They are a reading snapshot, not a vendored archive,
signed attestation or guarantee of future availability. Failed/relocated discovery URLs are
not presented as successfully verified documentation.

## Æion and governance context

| ID | Primary source | Inspected use and limit |
| --- | --- | --- |
| AE-01 | [Æion Factory — CRAFTED](https://github.com/OualidGuennif/aeion-factory/blob/00fdbd0757b8ed3e08e71fa335de851234423c74/efficiency/CRAFTED.md) | Existing local instructions/CRAFTED and public foundation; retain development workflow |
| AE-02 | [Æion CROA](https://github.com/OualidGuennif/aeion-croa) | Current local component, credits and pinned upstream catalog; audit kit, not runtime enforcement |
| AE-03 | [CROA v1.0.1 architecture, pinned source](https://github.com/CROA-Project/CROA/blob/4d59192da9a0d00412c9d2ccb9e5ab68176803ff/spec/parts/part-2-reference-architecture.md) | Relevant governance/durable evidence principles; not a new full conformance audit |

Also read the sibling Agentic OPS proposal and its minimal event/cost contract. That is local
design context, not a primary external standard or an implemented enforcement layer.

## Telemetry standards and collection

| ID | Primary source | Inspected use and limit |
| --- | --- | --- |
| ST-01 | [OTel GenAI overview](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/README.md) | Status Development; separate source repository; commit pinned |
| ST-02 | [OTel client inference](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/client-inference.md) | Selected identity, request/response, reasoning and timing conventions |
| ST-03 | [OTel agent/framework spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/gen-ai-agent-spans.md) | Selected agent/workflow/tool hierarchy; generated tables not a universal harness implementation |
| ST-04 | [OTel inference token metrics](https://github.com/open-telemetry/semantic-conventions-genai/blob/9ffc7e00c639be7712e544e3e54331e885dccf84/docs/gen-ai/gen-ai-token-metrics.md) | Counters versus per-operation distributions; cache/reasoning subset semantics |
| ST-05 | [Collector resiliency](https://opentelemetry.io/docs/collector/resiliency/) | Queues, retry, persistent storage and remaining loss conditions |
| ST-06 | [Collector security practices](https://opentelemetry.io/docs/security/config-best-practices/) | Relevant receiver/configuration/resource security; actual deployment untested |
| ST-07 | [Arize OpenInference](https://github.com/Arize-ai/openinference) | Instrumentation/conventions overview, Apache-2.0 repository; mapping must be tested |

The fetched model-span/metrics documents complement ST-02–04. The framework deliberately uses a
versioned mapping instead of declaring every GenAI attribute stable.

## Harnesses and evaluation practice

| ID | Primary source | Inspected use and limit |
| --- | --- | --- |
| HA-01 | [Claude Code monitoring](https://code.claude.com/docs/en/monitoring-usage) | Native telemetry, beta spans, token categories, attempts, content/identity gates; exact local capture untested |
| HA-02 | [Claude Code model configuration](https://code.claude.com/docs/en/model-config) | Model/effort controls, fallback/configuration scope; not proof of arbitrary remote controller access |
| HA-03 | [Claude Agent SDK Python](https://code.claude.com/docs/en/agent-sdk/python) | `ClaudeSDKClient.set_model`, session/options reference; no blanket subscription or cross-provider qualification |
| HA-04 | [Anthropic effort](https://platform.claude.com/docs/en/build-with-claude/effort) | `output_config.effort`, model dependence and cache/change semantics |
| HA-05 | [Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Outcome versus transcript, grader types, calibration and isolation; selected evaluation sections |
| HA-06 | [Infrastructure noise in agentic coding evals](https://www.anthropic.com/research/infrastructure-noise) | Resource and environment confounding; findings not reproduced here |
| HA-07 | [OpenAI agent evaluations](https://developers.openai.com/api/docs/guides/agent-evals) | Traces, graders and repeatable datasets; not a provider-neutral enforcement mechanism |

HA-05 is authored by Mikaela Grace, Jeremy Hadfield, Rodrigo Olivares and Jiri De Jonghe;
HA-06 by Gian Segato, with collaborators credited upstream.

## OpenRouter

| ID | Primary source | Inspected use and limit |
| --- | --- | --- |
| OR-01 | [Provider selection](https://openrouter.ai/docs/guides/routing/provider-selection) | Allowlist/fallback/parameter support, soft latency/throughput preferences and rate ceilings |
| OR-02 | [Parameters](https://openrouter.ai/docs/api/reference/parameters) | Supported setting names and omitted-versus-explicit behavior; actual model semantics need qualification |
| OR-03 | [Reasoning tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens) | Normalized reasoning controls, returned-content exclusion and model-specific constraints |
| OR-04 | [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models) | Advertised support/catalog fields, pricing and model metadata |
| OR-05 | [Endpoint API](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model) | Per-endpoint support, limits and observed performance fields; account permissions untested |
| OR-06 | [Usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting) | Final usage, native tokens, credits, details and deprecated no-effect flags |
| OR-07 | [Generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation) | Later usage lookup; availability/delay/retention and actual fields untested |
| OR-08 | [Broadcast](https://openrouter.ai/docs/guides/features/broadcast) | Asynchronous traces, root accounting, privacy mode and metadata; selected sections, destination mapping untested |
| OR-09 | [Zero data retention](https://openrouter.ai/docs/guides/features/zdr) | Endpoint-specific data handling; not a substitute for local content/egress control |
| OR-10 | [Claude Code integration](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration) | Base URL, bearer mapping/conflict handling and Anthropic-first-party compatibility caveat |
| OR-11 | [Agent SDK dynamic parameters](https://openrouter.ai/docs/agent-sdk/call-model/dynamic-parameters) | Parameter functions resolved at turn start in that SDK; not a stock CLI guarantee |
| OR-12 | [Capping shared agent keys](https://openrouter.ai/docs/guides/best-practices/capping-shared-agent-keys) | Scoped key limits; concurrent exposure/zero overshoot not demonstrated |

## DeepInfra

| ID | Primary source | Inspected use and limit |
| --- | --- | --- |
| DI-01 | [Chat Completions overview](https://docs.deepinfra.com/chat/overview) | Endpoint, parameters, tier/fail-fast behavior and model-dependent limits |
| DI-02 | [Chat Completions OpenAPI](https://docs.deepinfra.com/api-reference/chat-completions/openai-chat-completions) | Typed parameter definitions, wider reasoning enum, seed caveat and ignored feature behavior |
| DI-03 | [Reasoning models](https://docs.deepinfra.com/chat/reasoning) | Effort/object controls, output billing and unsupported-model no-effect warning |
| DI-04 | [Streaming](https://docs.deepinfra.com/chat/streaming) | Final-chunk usage and SSE shape; parser edge cases untested |
| DI-05 | [Prompt caching](https://docs.deepinfra.com/chat/prompt-caching) | Prefix reuse, model/account-scoped key and cached token examples |
| DI-06 | [Prompt cache retention](https://docs.deepinfra.com/chat/prompt-cache-retention) | Model-limited retention, TTL, write/read pricing and granularity |
| DI-07 | [Tool calling](https://docs.deepinfra.com/chat/tool-calling) | OpenAI-compatible tool flow; vendor performance claims not adopted |
| DI-08 | [Structured outputs](https://docs.deepinfra.com/chat/structured-outputs) | JSON object/schema modes and model dependence; local schema enforcement untested |
| DI-09 | [Anthropic SDK and Claude Code](https://docs.deepinfra.com/integrations/anthropic) | Compatible endpoints/auth/model mapping and feature caveat; not a validated complete Anthropic implementation |
| DI-10 | [Rate limits](https://docs.deepinfra.com/account/rate-limits) | Concurrency versus RPM and overload 429; actual account capacity untested |
| DI-11 | [Data privacy](https://docs.deepinfra.com/account/data-privacy) | Metadata logging, model-provider exceptions and bulk API distinction |

DI-02's broad effort enum differs from the narrower DI-03 guide. This discrepancy is intentionally
retained as a qualification question instead of resolved by assumption.

## Platforms, gateways and infrastructure

| ID | Primary source | Inspected use and limit |
| --- | --- | --- |
| TO-01 | [Langfuse OTel integration](https://langfuse.com/integrations/native/opentelemetry) | Trace endpoint, mapping and v4 ingestion guidance; selected sections, local ingestion untested |
| TO-02 | [Langfuse evaluations](https://langfuse.com/docs/evaluation/overview) | Scores, datasets, online/offline experiments, code/model/human evaluators |
| TO-03 | [Langfuse self-hosting](https://langfuse.com/self-hosting) | Docker pilot versus production and storage/worker architecture; not deployed |
| TO-04 | [Langfuse license](https://github.com/langfuse/langfuse/blob/main/LICENSE) | MIT core with enterprise/third-party exceptions; inspected source text |
| TO-05 | [Langfuse Claude Code integration](https://langfuse.com/integrations/developer-tools/claude-code) | Stop-hook transcript capture, content and private SDK internals; not installed |
| TO-06 | [Langfuse API migration](https://langfuse.com/faq/all/deprecated-api-migration) | Selected current/legacy endpoint rules and 2026-11-16 Cloud removal date |
| TO-07 | [Langfuse Halo](https://langfuse.com/docs/halo) | Analysis/resource assistant, approval/scope boundaries and beta self-hosting |
| TO-08 | [Phoenix repository](https://github.com/Arize-ai/phoenix) | Tracing/evaluation/datasets/self-hosting overview, not a deployment benchmark |
| TO-09 | [Phoenix license](https://github.com/Arize-ai/phoenix/blob/main/LICENSE) | ELv2 text including managed-service limitation; inspected source text |
| TO-10 | [MLflow tracing](https://mlflow.org/docs/latest/genai/tracing/) | GenAI/OTel observation overview; provider UI/advanced feature parity not assumed |
| TO-11 | [MLflow license](https://github.com/mlflow/mlflow/blob/master/LICENSE.txt) | Apache-2.0 source license; hosted offerings have separate scope |
| TO-12 | [OpenLIT repository](https://github.com/openlit/openlit) | OTel/agent observation and evaluation overview; Apache-2.0 repository, not installed |
| TO-13 | [LiteLLM routing](https://docs.litellm.ai/docs/routing) | Selected cost/latency/health/affinity strategies; source behavior and defaults need release pinning |
| TO-14 | [LiteLLM license](https://github.com/BerriAI/litellm/blob/main/LICENSE) | MIT core with enterprise exceptions; inspected source text |
| TO-15 | [vLLM Semantic Router system overview](https://vllm-sr.ai/docs/overview/semantic-router-overview/) | Current v0.4 docs: Envoy/router/control-plane boundaries; no integration run |
| TO-16 | [Semantic Router pipeline](https://vllm-sr.ai/docs/overview/signal-driven-decisions/) | Signals, eligible decisions, algorithms and plugins; not a sandbox/authorization certification |
| TO-17 | [Semantic Router license](https://github.com/vllm-project/semantic-router/blob/main/LICENSE) | Apache-2.0 source license |
| TO-18 | [New Relic AI monitoring](https://docs.newrelic.com/docs/ai-monitoring/intro-to-ai-monitoring/) | APM/token/cost/feedback facilities on supported instrumentation |
| TO-19 | [New Relic OTLP](https://docs.newrelic.com/docs/opentelemetry/best-practices/opentelemetry-otlp/) | Native ingest and protocol/configuration requirements; Æion span UI mapping untested |
| TO-20 | [Modal OTel integration](https://modal.com/docs/guide/otel-integration) | Audit/function log and resource/input-event export; not remote provider-internal telemetry |

License links are evidence of the inspected upstream terms, not a claim that all components,
commercial add-ons or future releases use identical terms. No backend was installed or compared
under load. No license-restricted upstream implementation is copied into this folder.

## Original routing and statistics research

| ID | Paper and authors | Reading depth, relevant result and limitation |
| --- | --- | --- |
| RE-01 | [FrugalGPT — Chen, Zaharia, Zou](https://arxiv.org/abs/2305.05176) | Abstract plus published-paper introduction/summary; cascade concept, not reproduced. [TMLR publication](https://lingjiaochen.com/papers/2024_FrugalGPT_TMLR.pdf) |
| RE-02 | [RouteLLM — Ong et al., v4](https://arxiv.org/abs/2406.18665v4) | Abstract and official repository usage; preference-based strong/weak routing, not task-success proof. [Repository](https://github.com/lm-sys/RouteLLM) |
| RE-03 | [RouterBench — Hu et al., v2](https://arxiv.org/abs/2403.12031v2) | Abstract/data-scope review; common routing outcomes, not executable counterfactual agent sessions |
| RE-04 | [Online Multi-LLM Selection — Poon et al.](https://arxiv.org/abs/2506.17670) | Abstract and problem/theoretical scope; contextual selection/myopic regret, not a long-horizon task guarantee |
| RE-05 | [SWE-Router — Son et al.](https://arxiv.org/abs/2607.00053) | Abstract and method figure/description; partial trajectories and restart branch; not reproduced |
| RE-06 | [ORACLE — Raj, Kundu, Joshi, Krishna, v4](https://arxiv.org/html/2607.22465v4) | Mechanism and implementation/replay/grading/pre-registration appendices; delayed task feedback/local scheduling; not reproduced |
| RE-07 | [WISERouter — Li, Gao, Lakshmanan, v1](https://arxiv.org/html/2607.23765v1) | Formulation, limitations and assumptions/experimental appendices; workload budget and exploration; not reproduced |
| RE-08 | [AgentRouter — Paul, Nandy](https://arxiv.org/abs/2609.22951) | Abstract only; emerging step-level routing report, no implementation audit or performance endorsement |
| RE-09 | [Doubly Robust Policy Evaluation and Learning — Dudík, Langford, Li, v2](https://arxiv.org/abs/1103.4601v2) | Abstract/problem scope; basis for later off-policy evaluation, not proof of valid Æion causal assumptions |
| RE-10 | [Confidence sequences — Howard, Ramdas, McAuliffe, Sekhon, v9](https://arxiv.org/abs/1810.08240v9) | Abstract/publication metadata and relevant sequential-inference scope; proofs not rederived |

SWE-Router authors: Seongho Son, Sangwoong Yoon, Jiahua Tang, Shuhan Wang, Lorenz Wolf and
Ilija Bogunovic. The current ORACLE v4 is dated 2026-10-01; older indexing uses TRACE-Router.
Do not merge results across those versions without reading the relevant methods.

The paper mechanisms inform the design; author-reported gains are not an Æion forecast. Full
research reproduction, implementation audits, benchmark leakage assessment and provider/hardware
transfer remain separate work.

## What remains unverified

No paid model calls, real-session transcript collection, provider bill reconciliation, deployed
OPS/CROA control test, backend installation, workload benchmark or controller canary was run.
The [qualification plan](../operations/implementation-plan.md) lists the evidence required to
change that status. Current external docs can drift; refresh selected releases before coding.

Attribution and license boundaries are summarized in [CREDITS](../../CREDITS.md).
