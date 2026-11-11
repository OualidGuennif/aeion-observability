---
type: Component
title: "Local agent observability and memory showcase"
description: "Flue + Pi agents in three execution tiers (in-memory triage, folder-confined local assistant, autonomous coding in OpenShell), a host-native cockpit with a counting relay, Markdown handover and four observation/memory tools."
status: draft
verified:
  - at: 2026-11-07
    what: "unittest live status: the report prints phase names and supervisor CI lines, and leaves reviewer prose out"
  - at: 2026-11-10
    what: "unittest stack and memory: claude-mem decommissioned in favor of deterministic local verified checkpoints, Hindsight 1.2.0 upgraded with reranking and PR evaluation post-mortems"
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

Make small agent workflows observable, verifiable and resumable. The host-native Python
cockpit/supervisor runs **Flue 2.3.0 + Pi 1.4.0** agent sessions in three execution tiers that
share every gate, memory and telemetry path:

| Tier (`runtime`) | Tools | Tasks | Verdict |
| --- | --- | --- | --- |
| 1 · Triage (`flue-just-bash`) | just-bash emulated shell over in-memory files; `submit_triage` | One frozen triage contract | Supervisor comparison, no sandbox |
| 2 · Local assistant (`flue-local`) | read/write/edit confined to the run workspace (writes in `src/`), strict skill, no shell | Four frozen Deno JavaScript contracts | Protected checks in OpenShell |
| 3 · Autonomous coding (`flue-openshell`) | bash/read/write/edit/grep/glob in OpenShell through a Flue sandbox adapter | Same four contracts | Protected checks in OpenShell |

Model calls leave from the host through the supervisor's counting relay. It tolerates up to 300s
of upstream silence before reporting `PROVIDER_TIMEOUT`; other socket failures are
`TRANSPORT_ERROR` and both are recognized run failures. The product under test is
the **Agora forum** (`demo/forum-app/`, Quarkus/Java). Nine observation services use Docker; a
private native mTLS gateway owns OpenShell sandboxes through its Docker compute driver. This is an
explicitly authorized local pilot, not a production OPS boundary or general model benchmark.
OpenShell is pinned at v0.1.7 (binaries, SDK and the sandbox/supervisor images by digest; read
2026-11-06 from the [v0.1.6](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.6) and
[v0.1.7](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.7) upgrade notes). The gateway
must now authenticate callers; its client CA turns on mTLS user authentication by default, so
no `allow_unauthenticated_users` opt-in is set. Sandbox and supervisor images move together
(the v0.1.6 control connection changed direction). The OCSF 1.8.0, Podman CA, MicroVM user
and shared-supervisor changes do not apply to this Docker-driver setup.
The controller loads the OpenShell gRPC client, so it sets `GRPC_ENABLE_FORK_SUPPORT=false`
before that import: otherwise every subprocess fork restarts gRPC threads that can abort the
child on macOS before its exec (`demo/app/grpc_fork.py`, test_grpc_fork).

The [operator cockpit](operator-cockpit.md) is the default page at `/` and `/factory`; the
model lab at `/lab` is a showcase and playground: it explains each stack piece (OpenShell
contains Flue + Pi, the relay counts model usage, OpenTelemetry feeds Langfuse, deterministic local checkpoints and
Hindsight 1.2.0 keep continuity) and its memory room only reads this observer's own checkpoints and
bounded Hindsight recall. Both pages share light/dark tokens. Current-contract completion locks selection. Historical
results for rewritten MDs remain visible without certifying the new contract. A dependency wait
names the missing IDs and clears only after their current contracts reach product main; it
does not impose a strictly numeric sequence. Active work exposes Prepare/Build/Check/Review/
PR-CI/Main stages, protected evidence and a full Langfuse build-session link. A model step
counts as the Build stage in that column once a preparation exists; the sentence under it
names the step. `python3 -m factory.live_status` from `demo/` prints those phase names
without receipts or reviewer prose.

Execution is explicit: `simulator`, a pinned deterministic `offline` fixture, or `live` with
automatic acceptance preparation and a Flue/Pi tier3 builder. Native admission qualifies tools
with scripted inference, independently of product delivery. Current protocol/freshness checks
guard catalog admission and role execution; an unstarted queued attempt is preserved during a
qualification pause. A named role loader consumes the provider credential; absence holds
`provider_unconfigured`. Pinned legacy targets still refuse another feature with
`target_feature_mismatch`. The [factory execution contract](factory-flue.md) owns the current
external product checker, frozen dependency policy, review independence and publication gates.
The owner authorized four workers on 2026-11-02 (`glm-5.3-flash`, `qwen-3.8-flash`,
`deepseek-4.1-flash`, `claude-haiku-5.5`) and added `gpt-6-luna` on 2026-11-06. On 2026-11-08
`minimax-m3.1-flash` replaced `mistral-large-4`. Internal display ids map to canonical wire ids and the
authoring choice is the shared router's deterministic result. A completed paid attempt is
`live_complete` with `simulated: false`, never `simulated_complete`.

Candidate Java checks run in a qualified, disposable Docker boundary: `--network none`, no Docker
socket, no host home or controller mount, only the candidate tree plus read-only Gradle caches,
non-root, read-only root filesystem, dropped capabilities, bounded CPU/memory/PIDs and a fixed
environment. The probe's image digest and denied network are recorded with the check; a missing
image or failed probe holds `sandbox_unqualified`. The checker detects a contract file altered
during its run. A verified pinned-base baseline (`demo/factory/baseline.py`) satisfies dependencies
only with hashed paths and an isolated passing base suite; a simulated receipt never does.

The current external product checker packages production before candidate unit tests and gives
tests a different workspace. Its app and Node/browser acceptance run in different PID/filesystem
namespaces over an owned disposable database loopback. The verifier sees neither source nor
database credentials. Native qualifications, real model results, protected merges and actual
PostgreSQL/React deployment remain distinct evidence. Obsolete mobile snapshot instructions
are historical; the current product roadmap is React DOM web.

## Data sources

Flue runtime events reduced to a metadata-only stream, independent Deno checks, artifact/Markdown
SHA-256, supervisor process events, official pinned tokenizer/chat-template files and Deno native
HTTP traces. Primary integration references, checked 2026-10-27:

- Flue at [`deee93b`](https://github.com/withastro/flue/tree/deee93b40d275ecc9a50c50af2158f20089d54bc) (v2.3.0):
  [sandboxes](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/sandboxes.md)
  (`local()` has no isolation by design; the just-bash virtual sandbox is isolated from host
  files, processes and environment variables, with network opt-in),
  [skills](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/skills.md),
  [tools](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/tools.md),
  [sandbox adapter API](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/reference/sandbox-api.md),
  [models and Pi providers](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/models.md),
  [runtime events](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/guide/observability.md)
  and its [OpenTelemetry adapter](https://github.com/withastro/flue/blob/deee93b40d275ecc9a50c50af2158f20089d54bc/apps/docs/src/content/docs/ecosystem/tooling/opentelemetry.md)
  (content on by default, therefore unused).
- [just-bash 3.6.0](https://www.npmjs.com/package/just-bash/v/3.6.0) (Apache-2.0): emulated
  commands including `jq`; without a network option `curl` is absent (observed).
- Pi [`@earendil-works/pi-ai` 1.4.0](https://www.npmjs.com/package/@earendil-works/pi-ai/v/1.4.0)
  OpenAI-completions compatibility flags (`supportsDeveloperRole`, `maxTokensField`,
  `supportsReasoningEffort`), observed on the wire with a local fake server.
- [OpenCode Go](https://github.com/anomalyco/opencode/blob/caebbcc0807e630629725f320f35a09aa4a427be/services/www/src/docs/content/console/go.mdx)
  client requirements (own user agent, stable `x-opencode-session`; Pi validated) and prices.
- [OpenShell telemetry](https://docs.nvidia.com/openshell/v0.1.7/observability/telemetry/),
  [Python SDK](https://docs.nvidia.com/openshell/v0.1.7/sdk/python/),
  [sandbox runtimes](https://docs.nvidia.com/openshell/v0.1.7/how-it-works/sandboxes/runtimes/) and the
  Docker driver [volume admission](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-core/src/resource_admission.rs)
  (operator labels; raw host paths refused) and [host-backed volumes](https://github.com/NVIDIA/OpenShell/blob/bdb956f2cd65a635f1294fccf1d138d263bf650f/crates/openshell-driver-docker/src/lib.rs)
  (`enable_bind_mounts`).
- [Langfuse OTLP](https://langfuse.com/integrations/native/opentelemetry), observations v2, native
  cost details and boolean scores. Current server pins are4.75.0; the prior4.49.0 schema
  qualification stays historical. The upgrade verifies actual migrations, metadata-only ingestion
  and preserved historical observations. Reasoning-effort enums survive both privacy filters;
  prompts, outputs and hidden reasoning remain excluded.
- [Hindsight configuration](https://hindsight.vectorize.io/developer/configuration) and the
  running 1.2.0 OpenAPI schema for retain/recall/documents with RRF reranking; `chunks` mode uses no extraction LLM.
- Deterministic local verified checkpoints with SHA-256 fingerprint deduplication (replacing claude-mem),
  including run-scoped observation readback and artifact integrity.

The [tokenizer manifest](../../demo/tokenizers.json) records immutable upstream revisions and
file fingerprints. No remote model code is executed and no coding-model weights are fetched.

## Inputs

One execution tier and one of its fixed versioned task contracts (four coding contracts, one
synthetic triage contract), an authorized Go key reference, approved model/profile,
active-input checkpoint (250k default), 300k admission budget, 4,096 output limit, framing
reserve, time/request/session limits and privacy policy. Free/Contributor models are excluded.
No host repository, global agent configuration or Docker socket is visible to the harness or
the sandbox. The original AEion dotenv is not mounted; only its explicitly authorized OpenCode
key is copied privately, and only the supervisor holds it.

## Outputs

- Coding tiers: verified JS artifact; 12 or 14 immutable Deno checks per
  task protect behavior, with the final verdict in a fresh OpenShell sandbox. Triage: a validated
  `result.json` scored per event against answers that never reach the harness.
- OTel traces to Langfuse, including native usage/cost estimates and quality/autonomy scores.
- Fsynced local metadata audit plus bounded OTLP/Docker logs, joined by run/trace/event identity.
- Read-back verified local checkpoints and Hindsight session-analysis memories in separate
  real/synthetic banks. Neither memory service receives a coding-provider credential. Hindsight also retains task-specific model-selection decisions and their run IDs as advisory snapshots.
- Cockpit KPIs per tier and task: all-attempt cost estimates, input/output tokens, median task time, verified
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
   Qwen/Haiku instead use complete API usage including cache to gate continuation: their byte
   bound reserves cost only, so a large estimate does not block launching bounded inputs.
   Unknown usage holds; native250k hands over and native input+output above300k fails. There is
   no independent first-request300k preflight guarantee for these closed-tokenizer profiles.
3. Native context >300k or a pinned-tokenizer discrepancy >20k fails the task and blocks live re-admission until
   requalification. Tokenizer parity/framing are explicit provider-qualification assumptions;
   do not claim knowledge of undisclosed provider internals or an invoice ceiling.
4. Close inference admission, delete/reap the old sandbox through OpenShell and wait for deletion,
   verify the MD, and start a new Flue conversation (fresh id, in-memory store) over preserved
   files/checks. Flue compaction is disabled and a compaction event fails the task. No opaque
   resume, generated summary, subagent, self-modifying harness or provider fallback is enabled.
5. Tier 3 agent tools and all generated-code verification execute only inside OpenShell, via the
   Flue adapter and the supervisor's loopback bridge (fixed argv commands). Tier 2 tools act on the
   host workspace folder: a tool-level restriction (no shell, path confinement, symbolic links
   refused, writes in `src/`), not OS isolation. Tier 1 tools are emulated in memory with no
   network configured. Flue's `local()` is used in no tier. Missing/expired security or harness
   qualification blocks live execution; no host or plain-Docker fallback exists for checks. The gateway propagates `OPENSHELL_TELEMETRY_ENABLED=false`.
   Immutable agent image IDs, the qualified agent UID, Landlock, one run subpath of the
   operator-labeled host-backed work volume and network mode `none` with no egress rule bound this
   local workload. Flue lists its `task` tool, but with no declared subagent every delegation is
   refused. After acceptance, the checked artifact stays under `demo/.local/work/published/` as
   evidence; no second application serves it, and that directory is not an OpenShell boundary.
6. Coding agents may write only the workspace `src/` directory. Config, verifier, reports and MD
   stay outside that writable scope, and expected check results never exist in the agent's image,
   workspace or harness input (they reach Deno on stdin; triage answers stay in the supervisor).
   Artifact/check evidence, not completion text, determines success.
7. Export no raw prompts/source/completions/reasoning/tool payloads/keys/arbitrary errors. The
   harness observer copies only usage numbers, finish labels, known tool names and outcomes; harness
   stdout/stderr are discarded. OTel reception and recalled memory have no authority over admission,
   permissions or acceptance.
8. Tiers are separate cohorts in KPIs and selection; campaigns run only tier 3. Include failed
   attempts and unresolved usage. No undefined denominator, absent feedback or
   missing charge becomes a zero-cost autonomous success. Recorded human assistance revises
   autonomy and its native score; it does not erase the verified artifact.

## Determinism

[Request boundary](../../demo/app/relay.py), [token budget](../../demo/app/token_budget.py),
[supervisor](../../demo/app/runner.py), [sandbox bridge](../../demo/app/bridge.py),
[harness provider](../../demo/flue/src/provider.ts), [harness observer](../../demo/flue/src/observe.ts),
[sandbox adapter](../../demo/flue/src/sandboxes/openshell.ts),
[folder-confined tools](../../demo/flue/src/sandboxes/restricted-local.ts),
[triage submission](../../demo/flue/src/tools/submit-triage.ts), [triage verdict](../../demo/app/triage.py),
[audit](../../demo/app/audit.py),
[memory adapter](../../demo/app/memory.py), [score adapter](../../demo/app/scores.py),
[KPI calculation](../../demo/app/kpis.py), [task-specific selection](../../demo/app/selection.py) and
[required sandbox boundary](../../demo/app/sandbox.py) use ordinary validated state, never an LLM vote.
Selection requires two complete autonomous successes per same-tier, same-task, same-method, 250k active-context cohort. Cost/time objectives are explicit and normalized deterministically. Ineligible or absent evidence uses a labeled provisional default. Model behavior and upstream service performance remain stochastic. The [forum service](../../demo/forum-app/src/main/java/local/aeion/forum/ThreadsResource.java)
and [cockpit](../../demo/app/server.py) separate the observed workload from its controls.

## Acceptance checks

The [runbook](../../demo/README.md) distinguishes offline regressions, real-harness/local-inference
qualification, real Go tasks, backend reads and UI checks. Its two purses are capped at $150 per
day, with $50 reserved for one author execution. Require MD-before-refusal ordering,
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
