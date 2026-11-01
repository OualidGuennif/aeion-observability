---
type: Reference
title: "OpenCode 300k admission experiment — 2026-10-26"
description: "Real paid DeepSeek V4.1 Flash transport, accounting and tool-continuation tests; narrow evidence, not an enabled Æion Factory strict profile."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.1
  at: 2026-10-26
sources:
  - id: evidence
    resource: ./opencode-context-qualification.json
    title: "Sanitized numeric results and experiment fingerprints"
  - id: runtime
    resource: https://opencode.ai/v2/docs/build/plugins/
    title: "Native HTTP, context, retry and WebSocket hooks"
  - id: native-source
    resource: https://github.com/anomalyco/opencode/blob/74f8d4860f49c563909e6b039b0cc8b454ebce72/packages/core/src/session/model-request.ts
    title: "Inspected request callback before HTTP handler"
  - id: tokenizer
    resource: https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/tree/314113f8a7dadb388215396ba5fbee2c610a04d6
    title: "Pinned official tokenizer and chat template"
---

# OpenCode 300k admission experiment

**Result: the tested primary HTTP path can refuse before transport, including after a real tool
result. An absolute Æion Factory-wide ceiling remains unqualified.** These tests used an isolated
experimental plugin, not the shipped Æion Factory plugin. `tools/agents/run --strict` still refuses.

## Scope and method

Æion Factory source was `a2edecdf48a25e1451912ca91d959fad62e2c1f7`. All model requests selected paid
`opencode-go/deepseek-v4.1-flash` through native OpenCode **2.1.4**, in a disposable repository
outside the configured Æion Factory ancestor. Each case used a fresh isolated native profile and the
managed launcher. Each experimental source snapshot had its own passing Graphify/Archify baseline.
No free auxiliary model was used: the title hook supplied a fixed title, retries were disabled,
and experimental WebSocket handshakes were refused. The runs used public synthetic text, not a
real engineering task or a model-quality benchmark.

An unconditional sentinel exception in `session.http.request` first established the actual native
denial path. The inspected source awaits this hook before calling its HTTP handler; the running
CLI surfaced the sentinel, exited nonzero and produced no HTTP-response callback. The following
cases counted a clone of the final serialized JSON request in that same hook. Unknown request
shapes and unavailable counters refused admission.

The counter reused an already installed, digest-pinned Observability image. Docker ran offline,
read-only and resource-limited; Æion Factory acquired no dependency or runtime configuration. The
image's official tokenizer/template hashes matched the pinned DeepSeek revision. Local rendering
counts messages and tool definitions, with the generation prefix. The experimental admission rule
was:

```text
rendered input tokens + maximum output tokens + 20,000 reserve < 300,000
```

The output maximum was verified in the final request as `max_completion_tokens`: 128 for text
cases, 512 for the tool case. Equality refused. This is a per-request context budget, not a limit
on cumulative tokens spent across a session. The reserve is conservative test policy, not a
provider-certified bound on hidden framing.

## Observed results

The [numeric evidence](opencode-context-qualification.json) records 12 cases and four real provider
responses: **577,728 input tokens and 158 output tokens** in total. These are usage counters, not
an invoice. Every fixture's tracked files remained unchanged during its native run.

| Case | Local input | Reserved budget | Observed result |
| --- | ---: | ---: | --- |
| Unconditional sentinel | not counted | not counted | Native refusal; no response callback |
| Small calibration | 7,958 | 28,086 | HTTP 200; provider input 7,958, output 38 |
| Larger calibration | 12,055 | 32,183 | HTTP 200; provider input 12,055, output 39 |
| Injected unavailable counter | unavailable | unavailable | Refused; no response callback |
| Injected unsupported validation key | not counted | unavailable | Refused; no response callback |
| Oversized prompt | 317,959 | 338,087 | Refused at limit; no response callback |
| Near-limit measurement | 278,859 | 298,987 | Measurement-only refusal; no paid response |
| Near-limit real call | 278,859 | 298,987 | HTTP 200; provider input 278,859, output 7 |
| Exact boundary | 279,872 | 300,000 | Refused at limit; no response callback |
| One below, measurement only | 279,871 | 299,999 | Measured only; admission not exercised |
| Tool-case measurement | 278,861 | 299,373 | Measurement-only refusal; no paid response |
| Real tool continuation | 278,861 → 281,601 | 299,373 → 302,113 | First call HTTP 200; read completed; second call refused |

The three text-only provider input counts exactly matched the local counts. With the read-tool
definition, the provider reported **278,856**, five fewer than the local **278,861**. Its 74 output
tokens stayed below the 512-token reservation. After the native `read` completed, the final next
request contained system/user/assistant/tool messages. Its locally counted budget crossed 300k;
the hook refused with `FACTORY_300K_LIMIT` and there was no second response callback. The prototype
also capped attempts at one forwarded call per case; this continuation independently exceeded the
numeric limit, rather than relying only on that spend cap.

## What this establishes

- A running OpenCode 2.1.4 primary HTTP request can be stopped before its handler sends it on this
  paid route; discovery alone was not used as proof.
- A real request above 250k input was counted before transport and reconciled against provider
  usage. The output reservation held in all four paid responses.
- A real tool result caused another final-request count and a refusal before the next provider
  call. The request was not truncated or rewritten to make it fit.
- The exact local boundary and injected validation/counter failures refused execution.

## Remaining qualification work

The native docs describe HTTP hooks for primary, title, compaction and generate calls. Only
**primary** dispatch was exercised here; title was skipped, compaction/generate were not invoked,
and the WebSocket refusal was configured but not exercised. Other providers, models, native
versions, multimodal/stateful payloads, other plugins mutating a later hook, parallel sessions,
counter timeouts and recovery have no qualification from these cases.

This experiment did not exercise the 250k alert, durable handover verification or a real
compaction/resume cycle. Four accounting comparisons cannot prove arbitrary provider framing or
future tokenizer compatibility. The reused image is an experiment dependency, not a portable
Æion Factory counter installation. A production strict profile still needs a maintained counter and
fail-closed lifecycle/auxiliary-call tests before enabling a strict launch.

The private metadata-only results and plugin/driver snapshots are retained under ignored
`.aeion/qualification/context-300k/`; the public JSON pins fixture commits, plugin hashes and
individual result hashes. Hashes identify the local evidence; they are not an independent
attestation or a turnkey replay package. Raw model requests/responses and credentials are excluded
from these artifacts. The native CLI manages its own isolated session storage.
