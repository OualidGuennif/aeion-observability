# Pi sessions in Langfuse

Status: **installed nowhere yet; end-to-end transmission not verified on this machine.**
Owner request: prove that Pi sessions reach Langfuse (2026-11-01).

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

1. A Langfuse project and its two keys. The repository's own pilot (`demo/compose.yaml`) starts
   Langfuse, ClickHouse, Postgres, MinIO and Redis locally, but there is no `.env` in this checkout,
   so no keys exist yet.
2. A write to `~/.pi/agent/` (`pi install` and `langfuse.json`). The current sandbox is
   workspace-write, so that write is refused; it needs explicit approval.
3. One short Pi session, then the trace read back.

## Exact steps once approved

```bash
# 1. Install the extension (writes ~/.pi/agent/)
pi install npm:@langfuse/pi-observability-plugin

# 2. Point it at the Langfuse instance, without writing the secret to a file
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="http://127.0.0.1:3000"   # local pilot; cloud otherwise
export LANGFUSE_TRACING_ENVIRONMENT="development"

# 3. Run one session and confirm the status line says langfuse: on
pi "reply with the single word: ok"
```

Verification is a read of the backend, not a claim from the plugin: list the traces of that session
through the Langfuse API (`GET /api/public/traces?sessionId=<id>` with the same keys) or open
**Tracing → Sessions** in the Langfuse UI and check that the prompt, the generation with its token
count and the tool calls are present. The Pi status line shows `langfuse: off (no keys)` when
tracing is disabled or the keys are missing, which is the negative control.

## Risks and limits

- The extension records **raw prompts and outputs**. That contradicts this repository's default
  telemetry rule (no raw prompts in default telemetry), so it stays an explicit, local,
  owner-requested experiment: `environment=development`, a dedicated Langfuse project, and no
  production workload.
- It is marked experimental upstream; versions may break.
- Verified here: package metadata, install/credential mechanism and captured data, from the
  upstream README. **Not verified here:** an actual install and a trace read back, because no
  Langfuse keys exist in this checkout and the sandbox refuses writes to `~/.pi/agent/`.
