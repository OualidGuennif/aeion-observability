# Æion Observatory — the agent atelier

A local showcase connecting **OpenTelemetry, Langfuse, Hindsight and claude-mem** around real
**Flue + Pi** agent sessions. The cockpit/supervisor is Python and runs **natively on the
host**; the agent harness is **Flue 2.3.0 on Pi 1.4.0** in [three execution tiers](#three-execution-tiers):
triage in an emulated in-memory shell, a guided local assistant with folder-confined file tools,
and autonomous coding whose every tool call runs inside **NVIDIA OpenShell 0.1.5**. Generated
code from both coding tiers is checked in OpenShell. The product under test is the **Agora
forum** (Quarkus/Java); the old Deno/Hono playground is gone. The canonical product source is the
separate `aeion-autonomous-forum` checkout at
`demo/.local/factory/agents/aeion-autonomous-forum`; `demo/forum-app/` is a reading mirror. The
interface uses Æion's ivory, forest-green and copper palette, locally bundled fonts and a native
GPT Image illustration.

## Agora factory planning

The [Agora product plan](forum/PLAN.md), [factory contract](forum/ECOSYSTEM.md) and
[100 feature specs](forum/features/README.md) are revised designs. The [DeepSeek
handoff](forum/DEEPSEEK_HANDOFF.md) defines the local implementation sequence; [validation](forum/VALIDATION.md)
separates catalog checks from runtime qualification. This existing cockpit and its Flue harness
remain trusted infrastructure. Fake inference is the default and live/remote gates remain explicit.

The product itself is now real, not only planned: `demo/forum-app/` is a **Quarkus 3.40.1 / Java
25.0.4** service built with Gradle, carrying features 001-003 (skeleton and settings, migration
runner, test harness), the accounts and sessions ahead of their turn, and threads with a Kafka
producer and consumer behind a transactional outbox, CSRF tokens on every mutation, with 47 JUnit tests.
`demo/forum-db/` is the guardian service for its SQLite file: WAL, `VACUUM INTO` snapshots, a
restore drill and one-writer leasing. `demo/forum-mobile/` is the front on React Native 0.88.1
through Expo SDK 58: it typechecks, bundles for iOS (619 modules) and its API client passes a
12-step smoke test against the live service, though no simulator has run it. The same client also
renders in a browser through `react-native-web` (`npx expo start --port 8082` →
`http://127.0.0.1:8082`), which is how the forum is shown without a phone. A real Kafka broker
(`apache/kafka-native` in Docker) carried the event drill.

For a **local-only** container, the product repository now carries a multi-stage Dockerfile and
Compose service (`demo/forum-app/DOCKER.md` in that checkout). It publishes only
`127.0.0.1:8081`, stores SQLite in a named volume and refuses to start without an ephemeral
`AGORA_SESSION_SECRET`; health and feature-013 security headers are verified on a success and a
404. The image is never pushed; a VPS or any remote publication remains a separate owner decision.

## Start and show

From the repository root, with Docker running, Python 3.11+ and Node.js 22.19+. The native
gateway bootstrap supports macOS arm64 and Linux x86_64/arm64. Reserve memory for the nine
observation services plus transient sandboxes; the local machine used an 8 GB Docker
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

The factory's GitHub keys are described, with the exact permissions to attach, in the committed
root [`.env.example`](../.env.example) and in [runbook §5.1](factory/runbook.md#51-the-credentials-one-key-per-capability).
One key per capability: build, publish and release are three different keys, and no agent process
may hold more than the one it needs.

| View | Local address | Purpose |
| --- | --- | --- |
| Python cockpit | [localhost:8088](http://localhost:8088) | Session timeline, context, model KPIs, memory, MD and logs |
| Feature factory | [localhost:8088/factory](http://localhost:8088/factory) | Select, queue and watch forum feature builds |
| Forum API | [localhost:8081](http://127.0.0.1:8081/healthz) | Quarkus service: threads, accounts, health |
| Forum web front | [localhost:8082](http://127.0.0.1:8082) | React Native Web client (`npx expo start --port 8082`) |
| Langfuse | [localhost:3300](http://localhost:3300) | Real traces, generations, usage, estimated cost and boolean scores |
| Hindsight | [localhost:9999](http://localhost:9999) | Session-analysis memory banks and semantic recall |

Langfuse login: the address in `LANGFUSE_EMAIL` and its generated password in `LANGFUSE_PASSWORD`,
both in the private configuration (`demo/.local/stack.env`, written by `python3 demo/setup.py`).
Open it locally in an editor; never paste the password into chat/logs.
claude-mem and the OTel collector publish on loopback only for the native controller.
The first build downloads upstream runtimes and Hindsight's bundled local models, not model
weights for coding inference. Compose runs only the observation services; the forum, the
feature factory and the Flue harness run on the host.
The cockpit, counting relay and Flue harness run on the host; there is no controller container,
agent CLI image or Docker socket in this code path. A private native mTLS gateway owns OpenShell's
Docker compute driver. No user repository, host transcript or global agent setting is mounted.

Factory execution is explicit. The default `simulator` keeps the fake Markdown builder and says so
on the board. `AEION_FACTORY_EXECUTION=offline` loads the pinned forum profile and the shared
deterministic offline builder (real base, real write scopes, real protected check, no model call).
`AEION_FACTORY_EXECUTION=live` loads the same pinned target, the shared model catalog and the live
builder; the provider credential is read from the project's existing dotenv files and its absence
holds the build as `provider_unconfigured` instead of simulating. The owner authorized the four
workers (`glm-5.3-flash`, `qwen-3.8-flash`, `deepseek-4.1-flash`, `claude-haiku-5.5`) on 2026-11-02;
display ids are translated to canonical wire ids before every request.

Protected candidate checks run in a disposable Docker container: no network, no Docker socket, no
host home and no controller mount, only the candidate tree and read-only toolchain caches, with a
fixed environment, dropped capabilities and CPU/memory/PID limits. A probe records the image digest
and denied network before a build; a missing image or failed probe holds the build as
`sandbox_unqualified`. `demo/factory/baseline.py` verifies features already present at the pinned
base with hashed paths and the isolated base test suite, so feature 013 can queue against a
verified 001 baseline without a simulated merge receipt. A pinned target refuses any other feature
with `target_feature_mismatch`.

A useful presentation sequence:

1. **Play the handover demo**: synthetic usage crosses 230k/250k, a Markdown checkpoint appears,
   a fresh agent continues, and the four real local services capture/remember the task.
2. **Run Flue build**: choose an execution tier, then Auto or one of five paid Go profiles.
   Coding tiers edit `src/pricing.js` (through OpenShell in tier 3); 12 or 14 protected Deno
   checks run for the selected task in a fresh sandbox, then the supervisor records the result.
   Triage submits one labeled result per event, checked by the supervisor.
3. Compare the **same tier, task, gate and method version** in the model lab. Read cost/latency/autonomy
   together; declare human assistance when applicable rather than inferring independence.
4. **Recall session analyses**; inspect the checkpoint, correlated JSONL logs and Langfuse trace.

The replay is explicitly synthetic and does not call a paid model or pretend to be a harness
execution. The separate harness qualification below exercises the real Flue CLI against local
fake inference. Real provider runs and synthetic rows/banks are kept distinct.

## Execution boundary

| Layer | Where it runs | What it may do |
| --- | --- | --- |
| Cockpit, supervisor, relay | Host process, loopback only | Owns the Go key, counts and admits requests, writes MD/audit |
| Flue + Pi harness (`demo/flue`) | Host child process, scrubbed environment | Holds only per-session relay (and, in tier 3, bridge) tokens |
| Sandbox bridge (tier 3) | Host loopback, per-session token | Forwards nine file/shell verbs as fixed argv commands into one sandbox |
| OpenShell sandbox | Docker driver, Landlock, network `none` | Agent UID; one run subpath of the labeled work volume; writes only `src/`; no egress |

The harness's model calls leave from the host through the relay, so sandboxes need no network.
Flue's `local()` sandbox is unused in every tier: its documentation states it has no isolation
and its commands are real host processes. The adapter in `demo/flue/src/sandboxes/openshell.ts`
follows Flue's sandbox-adapter contract; OpenShell is not wired into the harness itself.

## Three execution tiers

| Tier (`runtime`) | Flue sandbox and tools | Tasks | Acceptance |
| --- | --- | --- | --- |
| 1 · Triage (`flue-just-bash`) | Flue `bash()` over just-bash 3.6.0: emulated shell, in-memory files, no network configured, `hardened` limits; plus `submit_triage` | `webhook-triage-v1` (8 synthetic events) | Supervisor compares each submitted result with frozen answers; no sandbox |
| 2 · Local assistant (`flue-local`) | `restricted-local`: read/write/edit on the run workspace only, writes only under `src/`, symbolic links refused; no shell, grep or glob; strict `local-change` skill | The four coding contracts | Protected Deno checks in OpenShell, final verdict in a fresh sandbox |
| 3 · Autonomous coding (`flue-openshell`) | OpenShell adapter: bash/read/write/edit/grep/glob in the sandbox through the bridge | The four coding contracts | Same as tier 2 |

All tiers share the relay, 230k/250k/300k gates, handover MD, observer, audit, telemetry and
memories. Tier 2 restricts the **model-facing tools, not the operating system**: the harness
process keeps the host user's privileges, so use tier 3 for unattended code changes. Tier 1's
harness receives only the events and label vocabulary; expected answers stay in the supervisor.
`submit_triage` accepts only known ids and labels, refuses an incomplete submission without
writing, and atomically replaces `result.json`, which the supervisor validates as untrusted input.
Flue documents just-bash as isolated from host files, processes and environment variables, with
network opt-in; none is configured, and the emulated shell has no `curl` (observed).
KPIs and Auto selection key cohorts by tier as well as task, so tiers are never pooled.
Comparison campaigns stay on tier 3.

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
aggregation, sorting and input mutation. They remain small synthetic coding tasks. Tier 1 has
one separate frozen contract: eight synthetic webhook events, each labeled with severity,
component, route and duplicate reference (one check per event).

**Compare all tasks & models** runs every available profile × 4 tasks × 2 repetitions (40 runs
while all five profiles are qualified), sequentially with rotated model order. Expired profiles
are neither run nor counted in the planned total. A $2 native-estimate monitor stops subsequent
runs; a per-task $0.10 budget also applies. Unknown usage, context violations or sandbox failure
stop the campaign. Unavailable/quota-restricted profiles are preserved as failures and skipped
thereafter.

Auto selection compares only real Flue evidence with the same execution tier, task, method
version (`flue-openshell-v1`) and 250k active-context gate. Earlier `openshell-go-v5` OpenCode cohorts
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

### Two independent daily purses ($15.00 each)

`demo/factory/budget.py` keeps one append-only JSONL journal with two scopes. The cockpit's live
runs spend from `aeion-observability`; the forum workers spend from `aeion-autonomous-forum`.
Each scope is capped at **$15.00 per local day** and one scope can never borrow from the other.
A run journals a reservation before it can call a model, then settles the actual cost; an open
reservation counts against the day, so two runs cannot spend the same last dollar. A missing,
corrupt or unreadable journal fails closed. The cockpit stops a live run with `BUDGET_STOP` and
the factory holds a build with `budget_unavailable` before opening a session or builder.

The default journal is `demo/.local/budget/ledger.jsonl` (mode `0600`); `AEION_BUDGET_LEDGER`
overrides it. Inspect the current day without spending:

```bash
python3 -m demo.factory.budget --ledger demo/.local/budget/ledger.jsonl
```

Only scope, day, USD amount, an opaque reservation id and a bounded note are stored: no prompt,
source, credential or provider response. The $15.00 limits are an owner decision; this ledger
does not grant permission for paid inference, and no paid call may run without a new explicit
owner approval.

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
and a compaction event fails the task. No subagent is declared: Flue still lists its `task` tool,
but every delegation is refused (verified) and the attempt is audited.

The default active input measure is native uncached input + cache read + cache write. It is
not cumulative spend. Both native reports and local preflight counts are logged with their
basis. Local tokenizer/template parity and the provider-framing reserve are qualification
assumptions, not a guarantee about undisclosed provider internals or invoices. A native
context >300k or count discrepancy >20k fails the task and blocks future live runs via
`demo/.local/data/context.blocked`; investigate/requalify before clearing it. The crossing native
report can exceed 250k, but no subsequent request is admitted.

## OpenShell qualification and protected checks

OpenShell admits mounts only by operator labels on a Docker volume, never a raw host path.
Bootstrap therefore creates the labeled `aeion-openshell-work` volume backed by `demo/.local/work`
(`enable_bind_mounts` allows that backing); each sandbox mounts only its run's subpath. An older
plain volume with that name is refused with removal instructions rather than deleted. OpenShell
qualification checks the configured agent UID, denied system writes, a read-only workspace with
writable `src/`, an invisible sibling folder of the same volume, denied outbound network,
workload network mode `none`, no Docker socket and propagated NVIDIA telemetry=false. On Linux
the agent UID is the host user (never root), so host-backed run folders stay owned by it; macOS
keeps UID 10001 under Docker Desktop's ownership mapping. The image holds only the file helper,
the check runner, Deno, Node, Python, ripgrep and git: no harness, model catalog or expected
results. Check cases travel to Deno on stdin. The authoritative verdict runs in a **fresh sandbox**
where no agent process ever ran; the MD's interim check uses the live sandbox and is labeled as such.

Security qualification expires in 24 hours. A separate harness qualification
(`demo/tests/qualify_flue.py`) binds the exact immutable agent image, agent UID and the
relay/bridge/runner/harness sources plus `package-lock.json`; live execution is blocked without
it. Rerun bootstrap and harness qualification after changes/expiry. Cleanup failure writes
`demo/.local/data/sandbox.blocked`; verify owned sandbox deletion and requalify before clearing it.
A killed qualification or a gateway restart can leave an OpenShell supervisor/sandbox pair running
with nothing tracking it. `demo/openshell/reap.py --older-than 3600` is a dry run of the cleanup;
add `--execute` to remove only containers carrying both OpenShell labels after that safety window.
Bootstrap also runs that sweep automatically, so a stale pair cannot survive the next install.
The gateway, Docker daemon and supervisor are trusted. OpenShell's local container driver is not
a microVM boundary or a production hostile-code qualification. After acceptance, the supervisor
keeps the checked artifact under `demo/.local/work/published/` as evidence; nothing serves it as
a second application, and that directory is not an OpenShell boundary.

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
relay, once per tier. Tier 3 (bridge, tools and checks in OpenShell): glob/grep/read/write in the
sandbox, the MD before the refused request at a native 250k report, preserved partial work, two
fresh conversations and 12/12. Tier 2: no shell/grep/glob offered, the strict skill loads, a write
outside `src/` is refused back to the model and leaves no file, then 12/12 in OpenShell. Tier 1:
`jq` sees the supplied events, host `/etc/passwd` is invisible, an incomplete submission is refused
without writing, then 8/8 with no sandbox event. Every tier asserts complete usage, no compaction,
no persisted conversation store and no prompt text in events; the marker requires all three. `--local-sandbox` runs the same chain with a host stand-in for
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
