# Pi sessions in Langfuse

Status: **verified end to end on the local stack, 2026-11-01**, with a local fake model so no
paid provider was called. Owner request: prove that Pi sessions reach Langfuse (2026-11-01).

## Verified upstream facts

Source: the package README (`https://github.com/langfuse/pi-observability-plugin`, fetched
2026-11-01) and the npm registry metadata (`@langfuse/pi-observability-plugin@0.1.2`, published
2026-08-31, MIT, author Langfuse).

- The extension listens to Pi's lifecycle events and sends **one Langfuse trace per user prompt**;
  the turns of one Pi session share one session ID, and turn numbering survives a restart.
- It records the user prompts, agent turns, model generations (inputs, outputs, cost, time to first
  token, token usage including cache-read and reasoning splits), every tool call (input, output,
  `ERROR` level on failure), thinking blocks, images, and nested subagent processes.
- Install: `pi install npm:@langfuse/pi-observability-plugin`; a single run without installing:
  `pi -e npm:@langfuse/pi-observability-plugin`.
- Credentials: `~/.pi/agent/langfuse.json` with `publicKey`, `secretKey` (required), optional
  `baseUrl` (default `https://cloud.langfuse.com`), `userId`, `environment`, `release`; or the
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`,
  `LANGFUSE_TRACING_ENVIRONMENT`, `LANGFUSE_USER_ID` environment variables, which take precedence.
- Kill switch: `LANGFUSE_TRACING_ENABLED=false` (one run, or exported); `pi config` switches the
  extension off; `pi remove npm:@langfuse/pi-observability-plugin` removes it.
- Requirements: Node.js 22+ (this machine runs Node 26.12.1) and `npm` on `PATH`.

## What this machine would need

1. A Langfuse project and its two keys. The repository's own pilot (`demo/compose.yaml`) **creates**
   them at first boot: `LANGFUSE_INIT_PROJECT_PUBLIC_KEY` / `..._SECRET_KEY` are seeded from the
   `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` of `demo/.local/stack.env`, written by
   `demo/setup.py`. That file is owner-only and must never be printed, committed or pasted.
2. A Pi agent directory. `PI_CODING_AGENT_DIR` relocates it, so the install lands in the ignored
   `.tmp/pi-agent/` instead of `~/.pi/agent/`; no write outside the repository is needed.
3. One short Pi session, then the trace read back.

## Exact steps once approved

```bash
# 1. Install the extension into the ignored repository-local agent directory
export PI_CODING_AGENT_DIR="$PWD/.tmp/pi-agent"    # already installed from the 0.1.2 probe
pi install npm:@langfuse/pi-observability-plugin

# 2. Point it at the host-published port, without writing the secret to a file
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="http://127.0.0.1:3300"   # demo/compose.yaml publishes 3300 -> 3000
export LANGFUSE_TRACING_ENVIRONMENT="development"

# 3. Run one session and confirm the status line says langfuse: on
pi "reply with the single word: ok"
```

Verification is a read of the backend, not a claim from the plugin. On **Langfuse v4 events_only**
the v1 read resources are gone — `GET /api/public/traces` and `/api/public/sessions` answer 404 —
so read `GET /api/public/v2/observations` (or **Tracing → Sessions** in the UI) and check that the
prompt, the generation with its token count and the tool calls are present. The Pi status line shows
`langfuse: off (no keys)` when tracing is disabled or the keys are missing, which is the negative
control.

## Observed on 2026-11-01

Run from `.tmp/pi-agent` against `http://127.0.0.1:3300` with a local OpenAI-compatible fixture
(`fixture/mock`, no paid call). Three sessions produced, in `environment=development`, three
`Conversational Turn` spans and three `LLM Call` generations, each generation carrying
`input=1234`, `output=56`, latency, time-to-first-token, a Pi session id and a trace id. The raw
prompt (58 characters) and the model output (35 characters) were attached, which is the privacy
trait this note already warns about. The observations were read back through
`GET /api/public/v2/observations`, not through the plugin's own status line.

## Risks and limits

- The extension records **raw prompts and outputs**. That contradicts this repository's default
  telemetry rule (no raw prompts in default telemetry), so it stays an explicit, local,
  owner-requested experiment: `environment=development`, a dedicated Langfuse project, and no
  production workload.
- It is marked experimental upstream; versions may break.
- **Two producers, one backend.** The supervisor already sends one metadata-only trace per run
  (`langfuse.session.id` = run id, `demo/app/telemetry.py`), while the extension writes one trace
  per prompt keyed by Pi's own session id. They are separate session views rather than duplicates,
  but summing both double-counts cost: keep the extension on `environment=development` and out of
  the demo's KPIs, and never merge its rows with the supervisor's.
- Verified here: package metadata, the install/credential mechanism and captured data from the
  upstream README; a repository-local install under `.tmp/pi-agent` (`PI_CODING_AGENT_DIR`); and a
  real transmission read back from the local Langfuse API (2026-11-01).
  **Not verified here:** a paid provider session, and the plugin against Langfuse Cloud.

## Decision — not adopted (2026-11-01)

The owner asked whether the extension adds anything Flue does not already give us. Measured answer:

- **Duplicated:** token usage, cache reads, model name, latency and per-turn spans. The supervisor
  already receives all of them from Flue's metadata observer (`demo/flue/src/observe.ts`), which
  emits `usage {input, output, cacheRead, cacheWrite, cost}` per turn and never copies prompts.
- **Unique, and unwanted:** the raw prompt and output text, plus time-to-first-token. The raw text
  is exactly what `AGENTS.md` rule 7 forbids in default telemetry, and TTFT does not justify a
  second producer that bypasses the collector's attribute allowlist.
- **Not needed:** standalone `pi` CLI coverage outside Flue. No workflow in this repository runs
  that way.

So the experiment is closed: the local install under `.tmp/pi-agent` was removed, and no code
path referenced it. The record above stays as evidence that the transmission was verified; it is
not a recommendation to reinstall it.
