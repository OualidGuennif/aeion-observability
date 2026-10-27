# Æion Observatory — the agent atelier

A local Docker showcase connecting **OpenTelemetry, Langfuse, Hindsight and claude-mem**
around real **OpenCode CLI build** sessions. The observer/cockpit is Python; the application
under test is **Deno JavaScript + Hono**. The interface uses Æion's ivory, forest-green and
copper palette, locally bundled fonts and a native GPT Image illustration.

## Start and show

From the repository root, with Docker running and Python 3.11+. The native gateway bootstrap supports macOS arm64 and Linux x86_64/arm64. Reserve memory for this eleven-service lab plus its transient sandboxes; the local machine used an 8 GB Docker VM shared with other projects, which caused startup delays under load:

```sh
python3 demo/setup.py --opencode-env /absolute/path/to/AEion/.env
python3 demo/openshell/setup.py
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml up -d --build
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml exec -T demo python3 /opt/demo/tests/qualify_cli.py
```

Omit `--opencode-env` for simulation only. Setup copies **OPENCODE_API_KEY only**, without
mounting the original dotenv or displaying its contents. It refuses to overwrite existing
credentials. The ignored `demo/.local/stack.env` is owner-only; do not print/commit/share it
or use `docker compose config` without `--quiet`.

| View | Local address | Purpose |
| --- | --- | --- |
| Python cockpit | [localhost:8088](http://localhost:8088) | Session timeline, context, model KPIs, memory, MD and logs |
| Deno/Hono playground | [localhost:8090](http://localhost:8090) | Quote API running the independently verified JS artifact |
| Langfuse | [localhost:3300](http://localhost:3300) | Real traces, generations, usage, estimated cost and boolean scores |
| Hindsight | [localhost:9999](http://localhost:9999) | Session-analysis memory banks and semantic recall |

Langfuse login: `demo@aeion.local`; its generated password is `LANGFUSE_PASSWORD` in the
private configuration. Open it locally in an editor; never paste the password into chat/logs.
claude-mem is internal only; the cockpit shows acknowledgements and retrieved checkpoints.
The first build downloads upstream runtimes, Hindsight's bundled local models and the
pinned tokenizers, not model weights for coding inference. The eleven observation/application services run in Docker. OpenCode and protected checks run only through **OpenShell 0.1.5**, using its Docker compute driver locally. A private native mTLS gateway owns Docker access; the controller and workload have no Docker socket.
No Docker socket, user repository, host transcript or global agent settings are mounted.

A useful presentation sequence:

1. **Play the handover demo**: synthetic usage crosses 230k/250k, a Markdown checkpoint appears,
   a fresh agent continues, and the four real local services capture/remember the task.
2. **Run OpenCode build**: choose Auto or one of five paid Go profiles. The actual CLI edits
   `src/pricing.js`; 12 or 14 protected Deno checks run for the selected task, then its Hono API is probed.
3. Compare the **same task, gate and method version** in the model lab. Read cost/latency/autonomy
   together; declare human assistance when applicable rather than inferring independence.
4. **Recall session analyses**; inspect the checkpoint, correlated JSONL logs and Langfuse trace.

The replay is explicitly synthetic and does not call a paid model or pretend to be a CLI
execution. The separate CLI qualification below exercises the real CLI against local fake
inference. Real provider runs and synthetic rows/banks are kept distinct.

## Four tools, four responsibilities

- **OpenTelemetry** transports explicit metadata spans and logs. Deno HTTP spans join the
  supervisor's task trace through W3C `traceparent`. No automatic transcript capture.
- **Langfuse 4.49.0** receives OTLP/HTTP with the v4 ingestion header. Native CLI USD estimates
  are mapped to generation cost details; correctness and autonomous completion are published
  as boolean API scores. Scores can have upstream processing delay; the cockpit's canonical
  outcome is immediate.
- **claude-mem 15.2.0**, source pinned at `93c82aac6ce14e1cbda02dff9aa4c16e0edfce57`, stores
  working checkpoints through its explicit save/read API. A fingerprint deduplicates replay.
  This is an isolated local worker adapter, not a global plugin or transcript watcher; no
  generation provider, cloud sync or Chroma is configured for this role. The Bun base image is
  digest-pinned; that commit has no root lockfile, so its semver-ranged packages resolve at build time.
- **Hindsight 1.1.0** retains deterministic session analyses in separate real/synthetic banks.
  `chunks` extraction, local embeddings and disabled automatic consolidation avoid duplicate
  LLM work. Its LLM provider is `none`; semantic/keyword fusion uses RRF without an additional
  neural reranker. This small metadata corpus does not justify that extra model's CPU and
  startup cost. Semantic recall works without further Go spending. A 40-second shutdown grace
  lets the embedded PostgreSQL complete its documented shutdown before Docker forces termination.
  Memory remains advisory and never rewrites gate policy, credentials or permissions.

## Model choice and cost accounting

The harness pins **OpenCode 1.19.4, `--agent build`** and five paid Go profiles: GLM 5.3
Flash, DeepSeek V4.1 Flash, GLM 5.3, GLM 5.2 and MiniMax M3.1 Flash. The broader catalog is
intentionally restricted to profiles with a pinned official tokenizer/template and compatible
chat/tool protocol. [Go documentation](https://opencode.ai/v2/docs/console/go/) lists no training
and zero-day retention for these profiles (checked 2026-10-27). DeepSeek's current agreement
expires October 31; that profile is refused afterward pending requalification. Region/account
restrictions remain enforced upstream. The lab never changes privacy, Extra Usage or subscription settings.

Four versioned contracts cover cart totals (12 checks), shipping rules, exact discount arithmetic
and cart normalization (14 checks each). They exercise validation, safe integers, boundaries,
aggregation, sorting and input mutation. They remain small synthetic coding tasks.

**Compare all tasks & models** runs every available profile × 4 tasks × 2 repetitions (40 runs
while all five profiles are qualified), sequentially with rotated model order. Expired profiles
are neither run nor counted in the planned total. A $2 native-estimate monitor stops subsequent runs; a per-task $0.10
monitor also applies. Unknown usage, context violations or sandbox failure stop the campaign.
Unavailable/quota-restricted profiles are preserved as failures and skipped thereafter.

Auto selection compares only real OpenShell evidence with the same task, method version and
250k active-context gate. Eligibility requires at least two completed runs, 100% recorded
autonomous success and complete positive cost/latency evidence. A run interrupted by a controller
restart keeps unknown usage, so its cohort stays ineligible; KPIs report it as `interrupted`. Cost and speed objectives select
one dimension; balanced equally weights cost and time normalized to the best observed value.
Ties use model ID. GLM Flash is explicitly provisional when no cohort qualifies. This selects
the best **observed** candidate for a task, with run IDs, not a general quality winner or a
statistically significant result. Failed and assisted attempts disqualify that cohort.
Campaign decisions and their evidence are retained in Hindsight as advisory snapshots.

Per agent: 360 seconds (including cold startup on a loaded local Docker VM), at most 12 forwarded requests, 4,096 maximum output tokens; at most
three agents/task and one active task. A $0.10 native-cost stop is an **after-response estimate
monitor**, not a guaranteed invoice cap. Go quota and Extra Usage are provider-account settings;
the demo does not change them. Missing native usage/cost remains unresolved, never a zero-cost
winner. Failed attempts count. Infrastructure and memory CPU costs are not included in the
model estimate. The four small contracts support exploratory comparisons only.

## Markdown before reset: 230k → 250k → 300k

1. **Prepare at 230k:** the supervisor writes `HANDOVER.md` with task, artifact SHA-256,
   independent checks and next action. It flushes/fsyncs the file and directory before ack.
2. **Relay at 250k:** the hook pauses before the next request, requests a fresh checkpoint and
   waits at most 20 seconds for the matching acknowledgement. Missing/stale acknowledgement
   never releases admission. The supervisor closes inference admission, asks OpenShell to delete and reap the whole old sandbox, waits for confirmed deletion, removes only its
   XDG runtime, verifies the MD hash and loads its bounded text into the fresh session before the first request.
   The new agent reads the preserved artifact.
3. **Independent 300k admission budget:** a credential-owning local relay counts the complete
   request using official tokenizer/chat-template revisions in `tokenizers.json`. It reserves
   output plus **20,000 tokens for provider framing**, refuses unknown/multimodal/stateful input
   and blocks proposals beyond the allocation **before forwarding**. The normal preflight
   also hands over at 250k, leaving additional headroom below 300k.

The waiting CLI cannot send an additional paid request. It has only a session-local relay
credential; the real Go key stays in the supervisor. The relay validates model/output limits,
serializes requests, does not retry or follow redirects, and preserves actual CLI identity
headers. Missing plugins receive no valid admission ticket. Auto compaction, hidden title/
summary models, subagents, shell and external-directory tools are disabled.

The default active input measure is native uncached input + cache read + cache write. It is
not cumulative spend. Both native reports and local preflight counts are logged with their
basis. Local tokenizer/template parity and the provider-framing reserve are qualification
assumptions, not a guarantee about undisclosed provider internals or invoices. A native
context >300k or count discrepancy >20k fails the task and blocks future live runs via
`/data/context.blocked`; investigate/requalify before clearing it. The crossing native report
can exceed 250k, but no subsequent request is admitted while the MD is being prepared.

OpenShell qualification checks actual UID 10001, denied system writes/outbound network,
workload network mode `none`, no Docker socket and propagated NVIDIA telemetry=false. The
workload mounts only its run subdirectory; mTLS server keys and the Go key stay outside it.
Its sole egress rule permits the pinned OpenCode binary to POST the counted relay endpoint.
The public model catalog is bundled and config is read-only to prevent runtime npm/catalog
downloads. The image also preinstalls ripgrep: OpenCode's `glob` and `grep` use the system
binary instead of attempting a blocked runtime download. CLI qualification exercises both
search tools before the read/write and handover sequence. No host CLI, plain Docker agent
execution or permissive fallback exists. After acceptance, the Hono playground imports the
published artifact in its read-only Docker container; Deno permissions limit it to
`/work/published` and the collector. That is not an OpenShell boundary.

Security qualification expires in 24 hours. A separate real-CLI/fake-inference qualification
binds the exact immutable agent image and gate/counter/protocol sources; live execution is
blocked without it. Rerun bootstrap and CLI qualification after changes/expiry. Cleanup failure
writes `/data/sandbox.blocked`; verify owned sandbox deletion and requalify before clearing it.
The controller mounts only the public CA, client credential bundle and qualification file.
The gateway, Docker daemon and controller are trusted. OpenShell's local container driver is
not a microVM boundary or a production hostile-code qualification.

## Evidence and logs

Each run preserves source, `HANDOVER.md` when required, verification and metadata reports.
The supervisor writes an owner-only, fsynced, sequenced JSONL audit before exporting events.
It includes trace/run identity, process lifecycle, token counts, preflight decisions, MD
preparation/acknowledgement, checks and memory results. The cockpit links the MD and audit.
Raw prompts, source, completions, hidden reasoning, tool payloads, headers and arbitrary
exceptions are excluded. Collector attributes are allowlisted and log bodies canonicalized.
OTLP logs additionally rotate in `otel-logs` (5 MB × three files); Docker logs are bounded.

The local audit survives a backend outage. Collector export queues are bounded in memory;
this pilot does not guarantee complete trace delivery or exactly-once accounting through
crashes. Do not claim runtime qualification merely from green health checks.

```sh
node --test demo/tests/gate.test.mjs
python3 -m unittest discover -s demo/tests -v
# Runtime tests skip on a host without the Docker-only dependencies/tokenizers:
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml exec -T demo python3 -m unittest discover -s /opt/demo/tests -v
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml exec -T demo python3 /opt/demo/tests/qualify_cli.py
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml exec -T demo python3 /opt/demo/tests/qualify_scenarios.py
python3 demo/verify_backend.py                       # latest successful real run
python3 demo/verify_backend.py --synthetic           # latest successful replay
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml ps
```

The CLI fixture disables the stdout threshold to prove the **hook itself** stops the next
request. It asserts MD-before-close ordering, preserved partial work, two fresh sessions,
retired runtime cleanup and 12/12 checks. The admission test refuses a >300k proposal without
contacting an upstream, including concurrent requests while the MD callback is held.
Neither fixture spends model quota. Do not spend 250k tokens just to animate a showcase.

## Stop and preserve

```sh
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml down
```

Data persists; one hundred tasks is the demo's report limit. Interrupted tasks are not retried
against a provider. Use `--volumes` only when deliberately discarding this demo's databases,
reports and artifacts. Never delete/recreate the private configuration while retaining the
initialized database volumes: credential rotation is a separate migration.

The native gateway is private to `demo/.local/openshell`; bootstrap verifies official release
checksums and pins runtime/supervisor digests. It uses `OPENSHELL_TELEMETRY_ENABLED=false` for
both the gateway and SDK probes. On Linux, mTLS and the relay bind to the Docker bridge address;
on macOS they publish on loopback with Docker's host routing. Do not expose the trusted gateway
or relay to a LAN. The gateway log rotates at bootstrap; no agent stdout is persisted there.
For shutdown, first finish/retire any active task, then stop the Compose stack and send SIGTERM
to the exact project gateway PID recorded in the private state directory. Never prune unrelated containers.
