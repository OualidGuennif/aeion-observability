# Æion Observatory — the agent atelier

A local Docker showcase connecting **OpenTelemetry, Langfuse, Hindsight and claude-mem**
around real **OpenCode CLI build** sessions. The observer/cockpit is Python; the application
under test is **Deno JavaScript + Hono**. The interface uses Æion's ivory, forest-green and
copper palette, locally bundled fonts and a native GPT Image illustration.

## Start and show

From the repository root, with Docker Desktop running (8 GB Docker memory was the local test target):

```sh
python3 demo/setup.py --opencode-env /absolute/path/to/AEion/.env
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml up -d --build
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
The first build downloads upstream runtimes, Hindsight's bundled local models and ~27 MB of
pinned tokenizers, not model weights for coding inference. All eleven services run in Docker.
No Docker socket, user repository, host transcript or global agent settings are mounted.

A useful presentation sequence:

1. **Play the handover demo**: synthetic usage crosses 230k/250k, a Markdown checkpoint appears,
   a fresh agent continues, and the four real local services capture/remember the task.
2. **Run OpenCode build**: choose GLM Flash or DeepSeek Flash from Go. The actual CLI edits
   `src/pricing.js`; twelve protected Deno checks run, then the Hono API is probed.
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
  generation provider, cloud sync or Chroma is configured for this role.
- **Hindsight 1.1.0** retains deterministic session analyses in separate real/synthetic banks.
  `chunks` extraction, local embeddings and disabled automatic consolidation avoid duplicate
  LLM work. Its LLM provider is `none`; semantic recall works without further Go spending.
  Memory remains advisory and never rewrites gate policy, credentials or permissions.

## Model choice and cost accounting

The qualified harness is **OpenCode 1.19.4, `--agent build`**. Models are fixed to
`opencode-go/glm-5.3-flash` (default) and `opencode-go/deepseek-v4.1-flash` (comparison).
Both advertise 1 M context and tool support. Go documents no training and zero-day retention
for these models, checked 2026-10-25. DeepSeek's current retention agreement expires October
31; the demo refuses that profile afterward until requalified. No free/Contributor model,
Zen fallback or subscription setting change is made.

GLM Flash is a small-task default with context headroom and low advertised rates. DeepSeek
Flash tests a cheaper-cache alternative. Kimi K2.7 Code's 262,144 context offers less headroom
for this particular checkpoint. These are engineering choices, not quality leaderboard claims.

Per agent: 180 seconds, at most 12 forwarded requests, 4,096 maximum output tokens; at most
three agents/task and one active task. A $0.10 native-cost stop is an **after-response estimate
monitor**, not a guaranteed invoice cap. Go quota and Extra Usage are provider-account settings;
the demo does not change them. Missing native usage/cost remains unresolved, never a zero-cost
winner. Failed attempts count. Infrastructure and memory CPU costs are not included in the
model estimate. The tiny single-function corpus supports exploratory comparisons only.

## Markdown before reset: 230k → 250k → 300k

1. **Prepare at 230k:** the supervisor writes `HANDOVER.md` with task, artifact SHA-256,
   independent checks and next action. It flushes/fsyncs the file and directory before ack.
2. **Relay at 250k:** the hook pauses before the next request, requests a fresh checkpoint and
   waits at most 20 seconds for the matching acknowledgement. Missing/stale acknowledgement
   never releases admission. The supervisor stops the old process group, removes only its
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

This is a synthetic local lab, not a qualified hostile-code/production OPS sandbox.

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
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml run --rm --no-deps demo python3 -m unittest discover -s /opt/demo/tests -v
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml run --rm --no-deps demo python3 /opt/demo/tests/qualify_cli.py
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

Data persists; twenty tasks is the demo's report limit. Interrupted tasks are not retried
against a provider. Use `--volumes` only when deliberately discarding this demo's databases,
reports and artifacts. Never delete/recreate the private configuration while retaining the
initialized database volumes: credential rotation is a separate migration.
