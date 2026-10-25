---
type: Component
title: "Local agent observability and memory showcase"
description: "A Docker-only Deno/Hono target and Python cockpit with OpenCode build, local admission, Markdown handover and four complementary observation/memory tools."
status: draft
sources:
  - id: framework
    resource: observability.md
    title: "Framework boundary"
  - id: runbook
    resource: ../../demo/README.md
    title: "Demo operation and evidence limits"
---

# Local agent atelier

## Intent

Make a small coding workflow observable, verifiable and resumable. The Python cockpit/supervisor
runs OpenCode CLI build sessions against a synthetic Deno JavaScript pricing module. A Hono
application serves the accepted artifact. All eleven services run in Docker; this is an
explicitly authorized local pilot, not a production OPS boundary or general model benchmark.

## Data sources

Native OpenCode 1.19.4 JSON events, independent Deno checks, artifact/Markdown SHA-256, supervisor
process events, official pinned tokenizer/chat-template files and Deno native HTTP traces.
Primary integration references, checked 2026-10-25:

- [OpenCode Go](https://opencode.ai/docs/go/), the pinned
  [plugin interface](https://github.com/anomalyco/opencode/blob/v1.19.4/packages/plugin/src/index.ts),
  [pre-dispatch loop](https://github.com/anomalyco/opencode/blob/v1.19.4/packages/opencode/src/session/prompt.ts)
  and [CLI identity headers](https://github.com/anomalyco/opencode/blob/v1.19.4/packages/opencode/src/session/llm/request.ts).
- [Langfuse OTLP](https://langfuse.com/integrations/native/opentelemetry) and the installed
  4.49.0 OpenAPI schema, including observations v2, native cost details and boolean scores.
- [Hindsight configuration](https://hindsight.vectorize.io/developer/configuration) and the
  running 1.1.0 OpenAPI schema for retain/recall; `chunks` mode uses no extraction LLM.
- [claude-mem explicit saves](https://github.com/thedotmack/claude-mem/blob/93c82aac6ce14e1cbda02dff9aa4c16e0edfce57/src/services/memory/save-memory.ts),
  including project-scoped fingerprint deduplication and observation readback.
- [Deno OpenTelemetry](https://docs.deno.com/runtime/fundamentals/open_telemetry/) and
  [Hono/Deno](https://hono.dev/docs/getting-started/deno).

The [tokenizer manifest](../../demo/tokenizers.json) records immutable upstream revisions and
file fingerprints. No remote model code is executed and no coding-model weights are fetched.

## Inputs

A fixed `pricing-js-v1` contract, an authorized Go key reference, approved model/profile,
active-input checkpoint (250k default), 300k admission budget, 4,096 output limit, framing
reserve, time/request/session limits and privacy policy. Free/Contributor models are excluded.
No host repository, global agent configuration or Docker socket is mounted. The original
AEion dotenv is not mounted; only its explicitly authorized OpenCode key is copied privately.

## Outputs

- Verified JS artifact and live Hono quote API; twelve immutable Deno checks protect behavior.
- OTel traces to Langfuse, including native usage/cost estimates and quality/autonomy scores.
- Fsynced local metadata audit plus bounded OTLP/Docker logs, joined by run/trace/event identity.
- Read-back claude-mem working checkpoints and Hindsight session-analysis memories in separate
  real/synthetic banks. Neither memory service receives a coding-provider credential.
- Cockpit KPIs: all-attempt cost estimates, input/output tokens, median task time, verified
  autonomous completion, unknown exposure, human assistance and comparable profile versions.

## Invariants

1. Prepare/fsync `HANDOVER.md` at 230k. At 250k, pause before dispatch, refresh the MD and require
   its matching acknowledgement before retirement. Timeout/stale ack never opens admission.
2. The independent relay counts the complete candidate request with pinned official tokenizers,
   reserves output +20k framing, and refuses unknown or >300k allocations before forwarding.
   Normal preflight also hands over at 250k. No additional request is admitted during the
   checkpoint callback. The real Go key stays outside the agent process.
3. Native context >300k or discrepancy >20k fails the task and blocks live re-admission until
   requalification. Tokenizer parity/framing are explicit provider-qualification assumptions;
   do not claim knowledge of undisclosed provider internals or an invoice ceiling.
4. Stop/reap the old process group, remove only its XDG runtime, verify the MD, and start a
   fresh session over preserved files/checks. No implicit compaction, opaque resume, generated
   summary, hidden title model, subagent or provider fallback is enabled.
5. The separate agent UID may edit only `src/pricing.js`. Config, verifier, reports and MD stay
   outside that writable scope. Artifact/check evidence, not completion text, determines success.
6. Export no raw prompts/source/completions/reasoning/tool payloads/keys/arbitrary errors. OTel
   reception and recalled memory have no authority over admission, permissions or acceptance.
7. Include failed attempts and unresolved usage. No undefined denominator, absent feedback or
   missing charge becomes a zero-cost autonomous success. Recorded human assistance revises
   autonomy and its native score; it does not erase the verified artifact.

## Determinism

[Gate policy](../../demo/gate-policy.mjs), [hook](../../demo/context-gate.mjs),
[request boundary](../../demo/app/relay.py), [token budget](../../demo/app/token_budget.py),
[supervisor](../../demo/app/runner.py), [audit](../../demo/app/audit.py),
[memory adapter](../../demo/app/memory.py), [score adapter](../../demo/app/scores.py) and
[KPI calculation](../../demo/app/kpis.py) use ordinary validated state, never an LLM vote.
Model behavior and upstream service performance remain stochastic. The [target](../../demo/playground/main.js)
and [cockpit](../../demo/app/server.py) separate the observed workload from its controls.

## Acceptance checks

The [runbook](../../demo/README.md) distinguishes offline regressions, real-CLI/local-inference
qualification, real Go tasks, backend reads and UI checks. Require MD-before-close ordering,
fresh session identity, preserved partial files, missing-ack refusal, >300k preflight refusal,
known/unknown accounting, actual Langfuse generations/costs, memory readback/recall and
metadata-only log correlation. The [backend verifier](../../demo/verify_backend.py) checks
received observations rather than inferring ingestion from a green health endpoint.

## Out of scope

Production deployment, hostile-code qualification, arbitrary repository tasks, global hooks,
model-quality/savings claims, subscription-setting changes, invoice reconciliation, automatic
policy learning/promotion, durable exactly-once telemetry and changes to Factory/OPS/CROA.
The experimental CLI hook and any changed provider/tokenizer/model tuple must be requalified.
