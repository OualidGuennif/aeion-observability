---
type: Reference
title: "Provider and harness capability matrix"
description: "Verified OpenRouter/DeepInfra APIs, model-dependent parameter semantics, CLI/SDK actuation limits and the qualification work needed before adaptation."
status: draft
sources:
  - id: register
    resource: sources.md
    title: "Official sources and inspected versions"
---

# Provider and harness capabilities — 2026-10-23

Documented functionality below has **not** been exercised against paid inference endpoints.
`documented` is not `qualified`. Model slugs, support flags, prices and service availability
must be refreshed for the exact tuple selected for implementation.

## 1. Choose the actuation path explicitly

| Path | Observe | Set at launch / task boundary | Adapt within execution | Important limit |
| --- | --- | --- | --- | --- |
| Claude Code + subscription/token | Native OTel where enabled; task outcome checks | Supported model/effort choices | Supported user/CLI controls; unattended external control not established here | No arbitrary OpenRouter/DeepInfra routing using a Claude subscription |
| Claude Code + OpenRouter Anthropic-compatible API | Native harness telemetry plus router usage/Broadcast | Endpoint, token reference, model mappings | Only controls actually exposed by harness or qualified mediation | OpenRouter guarantees Claude Code compatibility only with Anthropic first-party provider |
| Claude Code + DeepInfra Anthropic-compatible API | Native harness signals plus translated response usage | Endpoint and model-slot mapping | Requires exact harness/protocol/model qualification | Anthropic-specific features may be unsupported |
| Claude Agent SDK wrapper | Documented session/result/OTel facilities | Options and configured model | Python `ClaudeSDKClient.set_model()` exists | Does not establish arbitrary effort/parameter changes or subscription eligibility |
| Direct OpenRouter/DeepInfra API adapter | Request/stream/response metadata under adapter control | Full supported request profile | Next-request parameter/model choice | Adapter owns session/tool/state compatibility and budget/cancel correctness |

Evidence: [Claude model controls](https://code.claude.com/docs/en/model-config),
[SDK model change](https://code.claude.com/docs/en/agent-sdk/python),
[OpenRouter Claude integration](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration),
[DeepInfra Anthropic integration](https://docs.deepinfra.com/integrations/anthropic).

Keep subscription observation as a supported design path. For broad automatic model/provider/
parameter experiments, use a qualified API-controlled path. Do not promise a shell environment
variable edit will change the next request of an already running CLI process.

## 2. OpenRouter

### Endpoints and catalog

Chat Completions: `https://openrouter.ai/api/v1/chat/completions`.
Claude-compatible base: `https://openrouter.ai/api` (the CLI adds its Messages path).
The Claude integration uses a bearer credential via `ANTHROPIC_AUTH_TOKEN` and explicitly clears
conflicting `ANTHROPIC_API_KEY`. Resolve secrets outside workload code where qualified; do not
copy example secret-bearing shell profiles into a public repo.
[Integration](https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration)

Use `/api/v1/models` for model metadata and
`/api/v1/models/{author}/{slug}/endpoints` for endpoint-specific capabilities, context/output
limits, pricing and available performance observations. Preserve the fetched snapshot/time and
units. Top-provider metadata is not proof of the endpoint that actually served a request.
[Models API](https://openrouter.ai/docs/api/api-reference/models/get-models),
[endpoint API](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model)

### Useful controls

| Control | Documented meaning | Æion treatment |
| --- | --- | --- |
| `model` / fallback model list | Requested model(s) | Explicit approved revisions where possible; model fallback is a treatment change |
| `provider.only`, `order`, `ignore` | Restrict/prioritize serving endpoints | Hard allowlist first; `order` alone must not stand in for it |
| `provider.allow_fallbacks` | Backup routing; documented default true | Explicit in qualified profiles; every fallback must remain authorized |
| `provider.require_parameters` | Restrict to parameter-supporting endpoints; default false | Require true for required controls; still verify semantics |
| `provider.sort` | Price, latency or throughput preference | Provider optimization, not task-quality estimation |
| `preferred_max_latency`, `preferred_min_throughput` | Prefer endpoints meeting recent performance thresholds | Soft preferences; failing endpoints remain possible fallbacks |
| `provider.max_price` | Filter accepted rate ceilings | Rate cap, not a session-spend cap; prompt/completion values are USD per million tokens |
| `provider.zdr`, `data_collection` | Endpoint data-handling filters | Hard profile constraints; no privacy downgrade to recover availability |
| `quantizations` | Endpoint precision filter | A separate qualified treatment, not a free interchangeable implementation detail |

[Provider-selection contract](https://openrouter.ai/docs/guides/routing/provider-selection)
documents that performance thresholds deprioritize rather than exclude. Its rolling provider
statistics are not an Æion-specific task SLO or a guarantee about the next request.

Some parameters can otherwise be ignored by endpoints. Required support filtering reduces that
risk but does not prove actual effective values. The catalog must also match protocol, tools,
structured output and continuation behavior.

### Reasoning and sampling

Use OpenRouter's documented `reasoning` object where supported. Effort and explicit token-budget
controls are model-dependent. `reasoning.exclude` controls returned reasoning content; it does
not establish that reasoning computation or billing is disabled. Preserve opaque reasoning/state
only in the protected harness path when required, never in the default telemetry export.
[Reasoning tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)

The parameters guide says omitted sampling settings are omitted upstream, leaving provider
defaults. Therefore “unset” must remain distinct from an explicit value such as `temperature=1`.
Tune only supported fields. Do not claim temperature zero guarantees identical distributed runs.
[Parameters](https://openrouter.ai/docs/api/reference/parameters)

### Usage and reconciliation

Chat Completions automatically includes usage, with the final SSE usage for streams. The old
`usage.include` and `stream_options.include_usage` switches are documented deprecated/no-effect.
Capture native token details and cost; interrupted streams may still lack the final record.
Generation-ID lookup supports later usage retrieval. Do not assume these fields are identical
in the Anthropic-compatible response received by Claude Code.
[Usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting),
[generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation)

Broadcast is asynchronous after completion. Use privacy mode per destination; allowlist custom
metadata because that remains exportable. Its root generation carries accounting totals; avoid
adding totals again from parent/attempt observations. Cost metadata can identify estimated usage
and upstream IDs, subject to interface availability. Qualify the exported destination schema.
[Broadcast](https://openrouter.ai/docs/guides/features/broadcast)

Key limits are useful defense in depth, but dashboard/key caps do not demonstrate atomic
in-flight admission with zero overshoot. Keep local reservations, deadlines and reconciliation
as separate requirements. [Agent key caps](https://openrouter.ai/docs/guides/best-practices/capping-shared-agent-keys)

## 3. DeepInfra

### Endpoints and schema

OpenAI-compatible base: `https://api.deepinfra.com/v1/openai`.
Anthropic-compatible base: `https://api.deepinfra.com/anthropic`, with Messages and count-tokens
endpoints documented. These are different wire protocols; do not send an OpenRouter `provider`
object to DeepInfra and expect provider routing.
[Chat overview](https://docs.deepinfra.com/chat/overview),
[Anthropic integration](https://docs.deepinfra.com/integrations/anthropic)

### Useful controls

| Control | Documented scope | Qualification required |
| --- | --- | --- |
| `model` | Named model, version/deployment forms in overview | Pin actual model identity; refresh model page/limits |
| `max_tokens` | Output limit; actual limit is model-dependent | Must leave room for required tools and reasoning; schema ceiling is not model capacity |
| `temperature`, `top_p` | Sampling settings in Chat Completions | Model support, actual acceptance and task effect |
| `reasoning_effort` / `reasoning` | Reasoning-capable models | Allowed values and behavior per model/protocol; unsupported model may ignore |
| `service_tier` | `priority` or `flex` on tagged models; omit for standard | Returned behavior, price and tail latency; not a universal parameter |
| `fail_fast` | Reject at capacity rather than queue where supported | Retry/fallback behavior and total deadline; 429 is not automatically a model-quality failure |
| `tools`, `tool_choice` | Tool use | Multi-turn round trips, tool-ID preservation and invalid/partial arguments |
| `response_format` | JSON/structured output on supported models | Actual schema enforcement and unsupported cases |
| `prompt_cache_key` | Account/model-scoped cache key | Tenant/session isolation and actual cache-hit behavior |
| `prompt_cache_options` | Explicit retention on listed supported models | Feature support, TTL/write premium and break-even reuse |
| `seed` | Request seed in API schema | Determinism explicitly not guaranteed |

Evidence: [Chat controls and tiers](https://docs.deepinfra.com/chat/overview),
[OpenAPI reference](https://docs.deepinfra.com/api-reference/chat-completions/openai-chat-completions),
[tool calling](https://docs.deepinfra.com/chat/tool-calling),
[structured output](https://docs.deepinfra.com/chat/structured-outputs).

### Documentation mismatch to preserve

The reasoning guide lists `none`, `low`, `medium`, `high`. The inspected API schema also lists
`minimal`, `xhigh`, `max`. Neither list establishes that every value works on every model.
Resolve against the exact model, schema and qualification result; keep disagreement visible in
the capability registry. Do not enable extra values merely because the broad schema accepts them.
[Guide](https://docs.deepinfra.com/chat/reasoning),
[schema](https://docs.deepinfra.com/api-reference/chat-completions/openai-chat-completions)

Reasoning counts toward output billing. Disabling or reducing it can affect tool choice and
task success, so the objective remains all-in task economics rather than short outputs.
Avoid setting both effort and a second reasoning object with conflicting intent.

### Service tiers and queueing

The current overview documents premium priority service, discounted best-effort flex service
and potentially long flex waits. These are promising experimental controls for speed versus cost,
with model tags and current pricing required. Do not choose flex for a short interactive deadline
merely because its token rate is lower. `fail_fast` may support deliberate client-side admission,
but a retry storm can erase its benefit. [Tier and queue semantics](https://docs.deepinfra.com/chat/overview)

The overview says unsupported tiers silently use standard service/pricing and that the response
reports the tier actually used. Compare requested and observed tier before attributing results.
It also gives `fail_fast` precedence over priority queueing; test combined settings explicitly.

The rate-limit guide describes concurrency per model and possible 429s under load even below
the nominal account limit. Read the actual account constraints; a concurrency ceiling is not an
RPM guarantee or a spending budget. [Rate limits](https://docs.deepinfra.com/account/rate-limits)

### Cache economics

Ordinary prefix caching and explicit retention are separate features. Retention documents
5-minute/1-hour windows on a limited model list with cache-write pricing and granularity.
Unsupported retention settings may be ignored. Use opaque scoped keys and verify cache use;
do not treat a cache key or a best-effort salt as the sandbox's security boundary.
[Prompt cache](https://docs.deepinfra.com/chat/prompt-caching),
[retention](https://docs.deepinfra.com/chat/prompt-cache-retention)

For a stable cacheable prefix of `P` tokens reused `n` times, a simplified prefill-only model is:

```text
without retention: n × P × standard_input_rate
with retention:    P × write_rate + (n - 1) × P × read_rate
```

Retention wins in this simplified model when `write_rate + (n-1)×read_rate < n×standard_rate`.
Include uncached remainder, actual retained blocks, changed prefixes, window renewals, model
switching and latency in the real estimate. A longer TTL is not always cheaper.

KV-prefix reuse is not replay of a previous response or external effect. Do not cache a passing
check across changed artifacts/policies or replay state-changing tool effects as an optimization.

### Usage and data handling

DeepInfra documents final-chunk streaming usage and cache detail fields. Preserve absent values
and qualify parser behavior when chunks have no choices, errors or interrupted connections.
Do not assume a native API `inference_status.cost` field exists in Chat Completions.
[Streaming](https://docs.deepinfra.com/chat/streaming),
[cache usage](https://docs.deepinfra.com/chat/prompt-caching)

The privacy page distinguishes general inference behavior from Google/Anthropic model exceptions
and bulk APIs; metadata logging includes request IDs, cost and sampling settings. It is not a
universal zero-retention guarantee across all features. Clarify retained-cache data lifetime for
the chosen profile as well. [Privacy policy](https://docs.deepinfra.com/account/data-privacy)

No documented per-request invoice-reconciliation endpoint was established for DeepInfra in
this research. Use a labelled token-rate estimate and separately authorized accounting export
if available; keep the unknown explicit.

## 4. Semantic intent to adapter mapping

| Intent | OpenRouter Chat Completions | DeepInfra Chat Completions | Stock Claude CLI |
| --- | --- | --- | --- |
| Less reasoning work | Qualified `reasoning.effort` | Qualified `reasoning_effort` or `reasoning.effort` | Supported `--effort` / session setting; not arbitrary API-field injection |
| Faster serving endpoint | Qualified provider sort/constraints | Qualified tier/model and queue behavior | Whatever selected gateway/harness exposes |
| Bound output | `max_tokens` where supported | `max_tokens` with model ceiling | Harness-supported cap; actual forwarded semantics tested |
| Preserve privacy | Endpoint filters + external egress policy | Qualified model/feature data policy + external egress | Auth/profile-specific data policy; content telemetry separately controlled |
| Reconcile a lost stream | Generation lookup where possible | No equivalent established here | Native estimate plus qualified provider-side evidence |
| Change model next turn | Adapter/SDK boundary | Adapter boundary | User controls or a qualified SDK/controller path |

Anthropic direct effort uses `output_config.effort`; that is not automatically the same payload
as either adapter's normalized reasoning settings. Its documentation also describes cache effects
when effort changes. Qualify changes on the chosen route instead of assuming identical cache
behavior through a gateway. [Anthropic effort](https://platform.claude.com/docs/en/build-with-claude/effort)

OpenRouter's Agent SDK documents parameter functions resolved at the start of each turn. This
is a concrete adaptation surface in **that SDK**, not a guarantee for stock Claude Code or an
arbitrary Chat Completions client. [Dynamic parameters](https://openrouter.ai/docs/agent-sdk/call-model/dynamic-parameters)

## 5. Minimal capability-registry entry

An implemented registry should record protocol, harness version, exact model/provider endpoint,
auth mode, parameter names/allowed values, context/output ceilings, tool/schema/stream support,
continuation constraints, cache behavior, data policy, price snapshot, advertised source/time,
qualification result/time and expiry. Unknown effective parameters remain null.

For each tuple test: ordinary response, streamed response, empty/error stream, final usage,
two tool cycles, malformed tool result, output truncation, retry, cancellation, model switch,
context limit, unsupported required field, privacy filters, cache reads/writes and lost-usage
reconciliation. Recheck after model, SDK, CLI, gateway or pricing changes.

The [request examples](../../examples/provider-requests.json) contain illustrative payload
fragments and placeholders. They are not production presets or successful API captures.
