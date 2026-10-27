# Æion Observatory — the agent atelier

A local showcase connecting **OpenTelemetry, Langfuse, Hindsight and claude-mem** around real
**Flue + Pi** coding-agent sessions. The cockpit/supervisor is Python and runs **natively on the
host**; the agent harness is **Flue 2.3.0 on Pi 1.4.0**; every agent tool call and every check
of generated code runs inside **NVIDIA OpenShell 0.1.5**. The application under test is **Deno
JavaScript + Hono**. The interface uses Æion's ivory, forest-green and copper palette, locally
bundled fonts and a native GPT Image illustration.

## Start and show

From the repository root, with Docker running, Python 3.11+ and Node.js 22.19+. The native
gateway bootstrap supports macOS arm64 and Linux x86_64/arm64. Reserve memory for the ten
observation/application services plus transient sandboxes; the local machine used an 8 GB Docker
VM shared with other projects, which caused startup delays under load:

```sh
python3 demo/setup.py --opencode-env /absolute/path/to/AEion/.env
python3 demo/install.py
python3 demo/openshell/setup.py
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml up -d --build
demo/.local/venv/bin/python demo/tests/qualify_flue.py
python3 demo/run.py
```

Omit `--opencode-env` for simulation only. Setup copies **OPENCODE_API_KEY only**, without
mounting the original dotenv or displaying its contents. It refuses to overwrite existing
credentials. The ignored `demo/.local/stack.env` is owner-only; do not print/commit/share it
or use `docker compose config` without `--quiet`. `install.py` creates the controller venv,
fetches the pinned tokenizers and runs `npm ci` for the locked Flue harness.

| View | Local address | Purpose |
| --- | --- | --- |
| Python cockpit | [localhost:8088](http://localhost:8088) | Session timeline, context, model KPIs, memory, MD and logs |
| Deno/Hono playground | [localhost:8090](http://localhost:8090) | Quote API running the independently verified JS artifact |
| Langfuse | [localhost:3300](http://localhost:3300) | Real traces, generations, usage, estimated cost and boolean scores |
| Hindsight | [localhost:9999](http://localhost:9999) | Session-analysis memory banks and semantic recall |

Langfuse login: `demo@aeion.local`; its generated password is `LANGFUSE_PASSWORD` in the
private configuration. Open it locally in an editor; never paste the password into chat/logs.
claude-mem and the OTel collector publish on loopback only for the native controller.
The first build downloads upstream runtimes and Hindsight's bundled local models, not model
weights for coding inference. Compose runs only the observation services and the playground.
The cockpit, counting relay and Flue harness run on the host; there is no controller container,
agent CLI image or Docker socket in this code path. A private native mTLS gateway owns OpenShell's
Docker compute driver. No user repository, host transcript or global agent setting is mounted.

A useful presentation sequence:

1. **Play the handover demo**: synthetic usage crosses 230k/250k, a Markdown checkpoint appears,
   a fresh agent continues, and the four real local services capture/remember the task.
2. **Run Flue build**: choose Auto or one of five paid Go profiles. The real agent edits
   `src/pricing.js` through OpenShell; 12 or 14 protected Deno checks run for the selected task
   in a fresh sandbox, then its Hono API is probed.
3. Compare the **same task, gate and method version** in the model lab. Read cost/latency/autonomy
   together; declare human assistance when applicable rather than inferring independence.
4. **Recall session analyses**; inspect the checkpoint, correlated JSONL logs and Langfuse trace.

The replay is explicitly synthetic and does not call a paid model or pretend to be a harness
execution. The separate harness qualification below exercises the real Flue CLI against local
fake inference. Real provider runs and synthetic rows/banks are kept distinct.

## Execution boundary

| Layer | Where it runs | What it may do |
| --- | --- | --- |
| Cockpit, supervisor, relay | Host process, loopback only | Owns the Go key, counts and admits requests, writes MD/audit |
| Flue + Pi harness (`demo/flue`) | Host child process, scrubbed environment | Holds only per-session relay and bridge tokens |
| Sandbox bridge | Host loopback, per-session token | Forwards nine file/shell verbs as fixed argv commands into one sandbox |
| OpenShell sandbox | Docker driver, Landlock, network `none` | Agent UID; reads the workspace, writes only `src/`; no egress at all |

The harness's model calls leave from the host through the relay, so sandboxes need no network.
Flue's `local()` sandbox is deliberately unused for this case: its documentation states it has
no isolation. The adapter in `demo/flue/src/sandboxes/openshell.ts` follows Flue's sandbox-adapter
contract; OpenShell is not wired into the harness itself.

## Four tools, four responsibilities

- **OpenTelemetry** transports explicit metadata spans and logs. Deno HTTP spans join the
  supervisor's task trace through W3C `traceparent`. Flue's own OpenTelemetry adapter is not used:
  it exports prompts, tool payloads and stacks by default. A metadata-only `observe()` subscriber
  feeds the supervisor instead.
- **Langfuse 4.49.0** receives OTLP/HTTP with the v4 ingestion header. Harness USD estimates
  are mapped to generation cost details; correctness and autonomous completion are published
  as boolean API scores. Scores can have upstream processing delay; the cockpit's canonical
  outcome is immediate.
- **claude-mem 15.2.0**, source pinned at `93c82aac6ce14e1cbda02dff9aa4c16e0edfce57`, stores
  working checkpoints through its explicit save/read API, with `platformSource: "pi"`. A fingerprint
  deduplicates replay. This is harness-independent: no generation provider, transcript capture,
  cloud sync, Chroma or OpenCode key is involved, and claude-mem's Pi extension (automatic prompt
  capture) is not installed. The Bun base image is digest-pinned; that commit has no root lockfile,
  so its semver-ranged packages resolve at build time.
- **Hindsight 1.1.0** retains deterministic session analyses in separate real/synthetic banks.
  `chunks` extraction, local embeddings and disabled automatic consolidation avoid duplicate
  LLM work. Its LLM provider is `none`; semantic/keyword fusion uses RRF without an additional
  neural reranker. This small metadata corpus does not justify that extra model's CPU and
  startup cost. Semantic recall works without further Go spending. A 40-second shutdown grace
  lets the embedded PostgreSQL complete its documented shutdown before Docker forces termination.
  Memory remains advisory and never rewrites gate policy, credentials or permissions.

## Model choice and cost accounting

The harness pins **Flue 2.3.0 (`@flue/runtime`, `@flue/cli`) and Pi `@earendil-works/pi-ai`
1.4.0**, with an exact `package-lock.json`, and five paid Go profiles: GLM 5.3 Flash, DeepSeek
V4.1 Flash, GLM 5.3, GLM 5.2 and MiniMax M3.1 Flash. A custom Pi provider points at the
supervisor's relay, never at Go directly. Models declare `reasoning: true` without an effort
parameter and `supportsDeveloperRole: false`, matching the previously qualified request shape.
Pi is a client the [Go documentation](https://opencode.ai/docs/go/) lists as validated. It sends
its own `User-Agent` and a stable `x-opencode-session`, which the relay forwards unchanged.
The broader catalog is intentionally restricted to profiles with a pinned official
tokenizer/template. Go lists no training and zero-day retention for these profiles (checked
2026-10-27). DeepSeek's current agreement expires October 31; that profile is refused afterward
pending requalification. Region/account restrictions remain enforced upstream. The lab never
changes privacy, Extra Usage or subscription settings.

Four versioned contracts cover cart totals (12 checks), shipping rules, exact discount arithmetic
and cart normalization (14 checks each). They exercise validation, safe integers, boundaries,
aggregation, sorting and input mutation. They remain small synthetic coding tasks.

**Compare all tasks & models** runs every available profile × 4 tasks × 2 repetitions (40 runs
while all five profiles are qualified), sequentially with rotated model order. Expired profiles
are neither run nor counted in the planned total. A $2 native-estimate monitor stops subsequent
runs; a per-task $0.10 budget also applies. Unknown usage, context violations or sandbox failure
stop the campaign. Unavailable/quota-restricted profiles are preserved as failures and skipped
thereafter.

Auto selection compares only real Flue/OpenShell evidence with the same task, method version
(`flue-openshell-v1`) and 250k active-context gate. Earlier `openshell-go-v5` OpenCode cohorts
remain historical evidence and never influence it. Eligibility requires at least two completed
runs, 100% recorded autonomous success and complete positive cost/latency evidence. A run
interrupted by a controller restart keeps unknown usage, so its cohort stays ineligible; KPIs
report it as `interrupted`. Cost and speed objectives select one dimension; balanced equally
weights cost and time normalized to the best observed value. Ties use model ID. GLM Flash is
explicitly provisional when no cohort qualifies. This selects the best **observed** candidate for
a task, with run IDs, not a general quality winner or a statistically significant result. Failed
and assisted attempts disqualify that cohort. Campaign decisions and their evidence are retained
in Hindsight as advisory snapshots.

Per agent: 360 seconds, at most 12 forwarded requests, 4,096 maximum output tokens; at most three
agents/task and one active task. Recovery from failure is deterministic and bounded: a fresh agent
receives the supervisor's MD and the preserved files, never a self-modified harness. Before every
forward, the relay waits until the supervisor has accounted the previous response, then refuses
if the $0.10 estimate budget or the native context gate is reached. Estimates use the profile's Go
rates (DeepSeek at its peak rate) and are not invoices. Go quota and Extra Usage are
provider-account settings; the demo does not change them. Missing native usage/cost remains
unresolved, never a zero-cost winner. Failed attempts count. Infrastructure and memory CPU costs
are not included in the model estimate. The four small contracts support exploratory comparisons only.

## Markdown before reset: 230k → 250k → 300k

1. **Prepare at 230k:** the supervisor writes `HANDOVER.md` with task, artifact SHA-256,
   current checks and next action. It flushes/fsyncs the file and directory before admitting
   the next request. The trigger is either the relay's local count or the previous native report.
2. **Close at 250k:** before forwarding, the relay refreshes the MD and refuses the request
   (local count ≥ 250k, or a native report ≥ 250k accounted by the admission barrier). The harness
   exits; the supervisor asks OpenShell to delete and reap the whole sandbox, waits for confirmed
   deletion, verifies the MD hash and starts a **new Flue conversation** (fresh id, in-memory
   store, compaction disabled) with the MD in its first message. The new agent reads the preserved
   artifact.
3. **Independent 300k admission budget:** the credential-owning relay counts the complete
   request using official tokenizer/chat-template revisions in `tokenizers.json`. It reserves
   output plus **20,000 tokens for provider framing**, refuses unknown/multimodal/stateful input
   and blocks proposals beyond the allocation **before forwarding**. The normal preflight
   also hands over at 250k, leaving additional headroom below 300k.

The harness has only a session-local relay token; the real Go key stays in the supervisor. The
relay validates model/output limits, serializes requests, does not retry or follow redirects,
and forwards only the client identity headers. Conversations live in an in-memory database and
the harness's stdout/stderr (which carry model text) are discarded. Flue compaction is disabled
and a compaction event fails the task. No subagents are declared.

The default active input measure is native uncached input + cache read + cache write. It is
not cumulative spend. Both native reports and local preflight counts are logged with their
basis. Local tokenizer/template parity and the provider-framing reserve are qualification
assumptions, not a guarantee about undisclosed provider internals or invoices. A native
context >300k or count discrepancy >20k fails the task and blocks future live runs via
`demo/.local/data/context.blocked`; investigate/requalify before clearing it. The crossing native
report can exceed 250k, but no subsequent request is admitted.

## OpenShell qualification and protected checks

OpenShell qualification checks the configured agent UID, denied system writes, a read-only
workspace with writable `src/`, an invisible unmounted host folder, denied outbound network,
workload network mode `none`, no Docker socket and propagated NVIDIA telemetry=false. On Linux
the agent UID is the host user (never root), so bind-mounted run folders stay owned by it; macOS
keeps UID 10001 under Docker Desktop's ownership mapping. The image holds only the file helper,
the check runner, Deno, Node, Python, ripgrep and git: no harness, model catalog or expected
results. Check cases travel to Deno on stdin. The authoritative verdict runs in a **fresh sandbox**
where no agent process ever ran; the MD's interim check uses the live sandbox and is labeled as such.

Security qualification expires in 24 hours. A separate harness qualification
(`demo/tests/qualify_flue.py`) binds the exact immutable agent image, agent UID and the
relay/bridge/runner/harness sources plus `package-lock.json`; live execution is blocked without
it. Rerun bootstrap and harness qualification after changes/expiry. Cleanup failure writes
`demo/.local/data/sandbox.blocked`; verify owned sandbox deletion and requalify before clearing it.
The gateway, Docker daemon and supervisor are trusted. OpenShell's local container driver is not
a microVM boundary or a production hostile-code qualification. After acceptance, the Hono
playground imports the published artifact in its read-only Docker container; Deno permissions
limit it to `/work/published` and the collector. That is not an OpenShell boundary.

## Evidence and logs

Each run preserves source, `HANDOVER.md` when required, verification and metadata reports.
The supervisor writes an owner-only, fsynced, sequenced JSONL audit before exporting events.
It includes trace/run identity, process lifecycle, token counts, preflight decisions, MD
preparation, checks and memory results. The cockpit links the MD and audit. Raw prompts,
source, completions, hidden reasoning, tool payloads, headers and arbitrary exceptions are
excluded; the harness observer copies only usage numbers, finish labels, known tool names and
outcomes. Collector attributes are allowlisted and log bodies canonicalized. OTLP logs
additionally rotate in `otel-logs` (5 MB × three files); Docker logs are bounded.

The local audit survives a backend outage. Collector export queues are bounded in memory;
this pilot does not guarantee complete trace delivery or exactly-once accounting through
crashes. Do not claim runtime qualification merely from green health checks.

```sh
demo/.local/venv/bin/python -m unittest discover -s demo/tests -v
(cd demo/flue && npm test)
demo/.local/venv/bin/python demo/tests/qualify_scenarios.py
demo/.local/venv/bin/python demo/tests/qualify_flue.py
python3 demo/verify_backend.py                       # latest successful real run
python3 demo/verify_backend.py --synthetic           # latest successful replay
```

`qualify_flue.py` runs the real Flue CLI and Pi against local fake inference through the real
relay and bridge, with tools and checks in OpenShell. It asserts glob/grep/read/write in the
sandbox, the MD before the refused request at a native 250k report, preserved partial work, two
fresh conversations, 12/12 checks, complete usage, no compaction, no persisted conversation store
and no prompt text in events. `--local-sandbox` runs the same chain with a host stand-in for
development and never writes the qualification marker. The admission test refuses a >300k
proposal without contacting an upstream, including concurrent requests while the MD callback is
held. Neither fixture spends model quota. Do not spend 250k tokens just to animate a showcase.

## Stop and preserve

```sh
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml down
```

Stop the cockpit with Ctrl-C after any active task finishes. Data persists in `demo/.local/data`
and `demo/.local/work`; one hundred tasks is the demo's report limit. Interrupted tasks are not
retried against a provider. Use `--volumes` only when deliberately discarding this demo's service
databases. Never delete/recreate the private configuration while retaining the initialized
database volumes: credential rotation is a separate migration.

The native gateway is private to `demo/.local/openshell`; bootstrap verifies official release
checksums and pins runtime/supervisor digests. It uses `OPENSHELL_TELEMETRY_ENABLED=false` for
both the gateway and SDK probes. On Linux, mTLS binds to the Docker bridge address; on macOS it
publishes on loopback. Do not expose the trusted gateway to a LAN. The gateway log rotates at
bootstrap; no agent stdout is persisted there. For shutdown, first finish/retire any active task,
then stop the cockpit and the Compose stack and send SIGTERM to the exact project gateway PID
recorded in the private state directory. Never prune unrelated containers.
