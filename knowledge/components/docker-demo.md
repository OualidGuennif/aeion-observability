---
type: Component
title: "Local agent observability and memory showcase"
description: "A Flue + Pi coding agent whose tools run only in NVIDIA OpenShell, a host-native Python cockpit with a counting relay, Markdown handover, a Docker Deno/Hono target and four complementary observation/memory tools."
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

Make a small coding workflow observable, verifiable and resumable. The host-native Python
cockpit/supervisor runs **Flue 2.3.0 + Pi 1.4.0** agent sessions against four frozen Deno
JavaScript contracts. Every agent tool call and every check of generated code executes inside a
mandatory NVIDIA OpenShell 0.1.5 sandbox through a Flue sandbox adapter; model calls leave from
the host through the supervisor's counting relay. A Hono application serves the accepted
artifact. Ten observation/application services use Docker; a private native mTLS gateway owns
OpenShell sandboxes through its Docker compute driver. This is an explicitly authorized local
pilot, not a production OPS boundary or general model benchmark.

## Data sources

Flue runtime events reduced to a metadata-only stream, independent Deno checks, artifact/Markdown
SHA-256, supervisor process events, official pinned tokenizer/chat-template files and Deno native
HTTP traces. Primary integration references, checked 2026-10-27:

- Flue at [`deee93b`](https://github.com/withastro/flue/tree/deee93b40d275ecc9a50c50af2158f20089d54bc) (v2.3.0):
  [sandboxes](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/sandboxes.md)
  (`local()` has no isolation by design),
  [sandbox adapter API](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/reference/sandbox-api.md),
  [models and Pi providers](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/models.md),
  [runtime events](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/observability.md)
  and its [OpenTelemetry adapter](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/ecosystem/tooling/opentelemetry.md)
  (content on by default, therefore unused).
- Pi [`@earendil-works/pi-ai` 1.4.0](https://www.npmjs.com/package/@earendil-works/pi-ai/v/1.4.0)
  OpenAI-completions compatibility flags (`supportsDeveloperRole`, `maxTokensField`,
  `supportsReasoningEffort`), observed on the wire with a local fake server.
- [OpenCode Go](https://github.com/anomalyco/opencode/blob/caebbcc0807e630629725f320f35a09aa4a427be/services/www/src/docs/content/console/go.mdx)
  client requirements (own user agent, stable `x-opencode-session`; Pi validated) and prices.
- [OpenShell telemetry](https://docs.nvidia.com/openshell/v0.1.5/observability/telemetry/),
  [Python SDK](https://docs.nvidia.com/openshell/v0.1.5/sdk/python/),
  [sandbox runtimes](https://docs.nvidia.com/openshell/v0.1.5/how-it-works/sandboxes/runtimes/) and the
  [Docker driver's bind mounts](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-driver-docker/src/lib.rs)
  (`enable_bind_mounts`).
- [Langfuse OTLP](https://langfuse.com/integrations/native/opentelemetry) and the installed
  4.49.0 OpenAPI schema, including observations v2, native cost details and boolean scores.
- [Hindsight configuration](https://hindsight.vectorize.io/developer/configuration) and the
  running 1.1.0 OpenAPI schema for retain/recall; `chunks` mode uses no extraction LLM.
- [claude-mem explicit saves](https://github.com/thedotmack/claude-mem/blob/93c82aac6ce14e1cbda02dff9aa4c16e0edfce57/src/services/memory/save-memory.ts),
  including project-scoped fingerprint deduplication, observation readback and the `pi` platform source.
- [Deno OpenTelemetry](https://docs.deno.com/runtime/fundamentals/open_telemetry/) and
  [Hono/Deno](https://hono.dev/docs/getting-started/deno).

The [tokenizer manifest](../../demo/tokenizers.json) records immutable upstream revisions and
file fingerprints. No remote model code is executed and no coding-model weights are fetched.

## Inputs

One of four fixed versioned task contracts, an authorized Go key reference, approved model/profile,
active-input checkpoint (250k default), 300k admission budget, 4,096 output limit, framing
reserve, time/request/session limits and privacy policy. Free/Contributor models are excluded.
No host repository, global agent configuration or Docker socket is visible to the harness or
the sandbox. The original AEion dotenv is not mounted; only its explicitly authorized OpenCode
key is copied privately, and only the supervisor holds it.

## Outputs

- Verified JS artifact and live Hono quote API; 12 or 14 immutable Deno checks per task protect
  behavior, with the final verdict in a fresh OpenShell sandbox.
- OTel traces to Langfuse, including native usage/cost estimates and quality/autonomy scores.
- Fsynced local metadata audit plus bounded OTLP/Docker logs, joined by run/trace/event identity.
- Read-back claude-mem working checkpoints and Hindsight session-analysis memories in separate
  real/synthetic banks. Neither memory service receives a coding-provider credential. Hindsight also retains task-specific model-selection decisions and their run IDs as advisory snapshots.
- Cockpit KPIs: all-attempt cost estimates, input/output tokens, median task time, verified
  autonomous completion, unknown exposure, human assistance and comparable profile versions.

## Invariants

1. Prepare/fsync `HANDOVER.md` at 230k (local count or previous native report) before admitting
   the next request. At 250k, refresh the MD and refuse the request before forwarding; the
   relay admits a request only after the supervisor has accounted the previous response.
2. The independent relay counts the complete candidate request with pinned official tokenizers,
   reserves output +20k framing, and refuses unknown or >300k allocations before forwarding.
   Normal preflight also hands over at 250k. No additional request is admitted during the
   checkpoint callback. The real Go key stays in the supervisor; the harness holds only
   per-session loopback relay and bridge tokens.
3. Native context >300k or discrepancy >20k fails the task and blocks live re-admission until
   requalification. Tokenizer parity/framing are explicit provider-qualification assumptions;
   do not claim knowledge of undisclosed provider internals or an invoice ceiling.
4. Close inference admission, delete/reap the old sandbox through OpenShell and wait for deletion,
   verify the MD, and start a new Flue conversation (fresh id, in-memory store) over preserved
   files/checks. Flue compaction is disabled and a compaction event fails the task. No opaque
   resume, generated summary, subagent, self-modifying harness or provider fallback is enabled.
5. Agent tools and generated-code verification execute only inside OpenShell, via the Flue
   adapter and the supervisor's loopback bridge (fixed argv commands). Flue's `local()` is not used
   for this case. Missing/expired security or harness qualification blocks execution; no host or
   plain-Docker fallback exists. The gateway propagates `OPENSHELL_TELEMETRY_ENABLED=false`.
   Immutable agent image IDs, the qualified agent UID, Landlock, a bind mount of the run folder only
   and network mode `none` with no egress rule bound this local workload. After acceptance, the Hono
   playground imports the published artifact in its read-only Docker container; Deno permissions
   limit it to `/work/published` and the collector. That is not an OpenShell boundary.
6. The agent UID may write only the workspace `src/` directory. Config, verifier, reports and MD
   stay outside that writable scope, and expected check results never exist in the agent's image or
   workspace (they reach Deno on stdin). Artifact/check evidence, not completion text, determines success.
7. Export no raw prompts/source/completions/reasoning/tool payloads/keys/arbitrary errors. The
   harness observer copies only usage numbers, finish labels, known tool names and outcomes; harness
   stdout/stderr are discarded. OTel reception and recalled memory have no authority over admission,
   permissions or acceptance.
8. Include failed attempts and unresolved usage. No undefined denominator, absent feedback or
   missing charge becomes a zero-cost autonomous success. Recorded human assistance revises
   autonomy and its native score; it does not erase the verified artifact.

## Determinism

[Request boundary](../../demo/app/relay.py), [token budget](../../demo/app/token_budget.py),
[supervisor](../../demo/app/runner.py), [sandbox bridge](../../demo/app/bridge.py),
[harness provider](../../demo/flue/src/provider.ts), [harness observer](../../demo/flue/src/observe.ts),
[sandbox adapter](../../demo/flue/src/sandboxes/openshell.ts), [audit](../../demo/app/audit.py),
[memory adapter](../../demo/app/memory.py), [score adapter](../../demo/app/scores.py),
[KPI calculation](../../demo/app/kpis.py), [task-specific selection](../../demo/app/selection.py) and
[required sandbox boundary](../../demo/app/sandbox.py) use ordinary validated state, never an LLM vote.
Selection requires two complete autonomous successes per same-task, same-method, 250k active-context cohort. Cost/time objectives are explicit and normalized deterministically. Ineligible or absent evidence uses a labeled provisional default. Model behavior and upstream service performance remain stochastic. The [target](../../demo/playground/main.js)
and [cockpit](../../demo/app/server.py) separate the observed workload from its controls.

## Acceptance checks

The [runbook](../../demo/README.md) distinguishes offline regressions, real-harness/local-inference
qualification, real Go tasks, backend reads and UI checks. Require MD-before-refusal ordering,
fresh conversation identity, preserved partial files, the pre-dispatch admission barrier, >300k
preflight refusal, known/unknown accounting, actual Langfuse generations/costs, memory
readback/recall and metadata-only log correlation. The [backend verifier](../../demo/verify_backend.py)
checks received observations rather than inferring ingestion from a green health endpoint.

## Out of scope

Production deployment, hostile-code qualification, arbitrary repository tasks, global hooks,
model-quality/savings claims, subscription-setting changes, invoice reconciliation, automatic
policy learning/promotion, self-modifying harnesses (Harness²-style recursion), durable
exactly-once telemetry and changes to Factory/OPS/CROA. Any changed harness, adapter,
provider/tokenizer/model tuple or image must be requalified.
