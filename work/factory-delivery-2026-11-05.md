# Factory delivery: verified progress and remaining work

The owner authorized the complete secure MD-to-main factory, real feature execution, a useful
cockpit, PostgreSQL/React delivery, current Langfuse diagnostics and GitHub branch cleanup.
This report distinguishes actual delivery, scripted mechanism checks and unfinished wiring.

## Published upgrade and branch hygiene

[PR19](https://github.com/OualidGuennif/aeion-observability/pull/19) is merged into main as
`48d1ae4173ca53685de4d65e7183714fd2553673`. Reviewed source head:
`32dc0cd3dbd91b3eda7a5ac56eb1485f698783cf`. Both GLM5.3Flash and Qwen3.8Flash approved both
complete packets with complete usage accounting. Original rejections and contextual follow-ups
are retained. The real Git transport-program gap was fixed, with9 failing regressions before
correction,728 passing hook checks and17 passing loop tests afterward.

Required PR checks passed. Both CI and Architecture refresh subsequently passed on the exact
merged main. Main requires linear history, so the attempted merge commit was refused and the
normal allowed squash method was used. No protection was disabled or bypassed. Main's tree
equals the reviewed develop tree. The84-commit history difference is not84 missing code changes.
Exact graph alignment of develop requires the owner's separate requested history-write approval.

Six unchanged topic heads matched their exact already-merged PR heads. All were archived as
`archive/2026-11-05/<branch>` tags, verified on GitHub, then removed atomically. Only main and
develop remain as remote branches. The pre-sync develop head is also preserved at
`archive/2026-11-05/develop-before-sync`. Private audit:
`demo/.local/maintenance/branch-cleanup-20261105.json`. No product/operator data was removed.

## Confirmed real-launch failure and correction

Real001 attempt `fc82028ad9604435952a74fc695a81dc` passed deterministic preparation, then failed
before any provider request. Its old summary discarded the execution detail and displayed only
builder_error. Metadata-only Langfuse readback identified CLI_FAILED, not a model failure.

The original public MD reproduced the failure with a real Flue CLI and local scripted endpoint:
zero requests reached the endpoint. Adding a sentence before YAML frontmatter made the same
task reach it once. The launcher passed a separate `--message` value beginning with `---`, which
the CLI parsed as flags. It now binds `--message=<value>`. The unchanged original MD then reached
the local endpoint once; scripted Done produced the expected NO_PATCH, not an invented patch.
This probe made zero real provider calls. The native automatic-preparation fixture now starts
with YAML frontmatter and exercises preparation, author handover, checks and independent votes.

Native capability admission v9 passed on protocol
`1061e7bc4d7d55c908735fc26780cc7f315a9ddaab2f43570d88060b7fd0117c`, evidence
`demo/.local/factory/admission-2ebq2_kc/proof.json`. It explicitly claims tools, not product delivery.
The safely reloaded controller admitted fresh real001 attempt
`85abd667488948ada3d5e819f73d3d80`. Its final result is pending; no feature merge is claimed here.

## Useful Langfuse diagnostics

Official references checked November5:

- [OTel ingestion and field mappings](https://langfuse.com/integrations/native/opentelemetry):
  retain the existing v4 ingestion header and explicit permitted metadata; costs belong to generations.
- [Levels and status messages](https://langfuse.com/docs/observability/features/log-levels):
  root failures must carry ERROR and an actual status message, not merely a metadata gate label.
- [Sessions](https://langfuse.com/docs/observability/features/sessions):
  group role traces with the same bounded session ID and link that session from the cockpit.
- [Public API](https://langfuse.com/docs/api-and-data-platform/features/public-api):
  bounded observation reads, explicit identity checks and selected field groups establish storage.

Build failure receipts now preserve frozen identity, preparation and exact role execution.
Root build spans include bounded failure code, phase, role/run/runtime, exit status, request/step
counts, known-cost completeness and execution trace ID. Their duration uses actual execution
elapsed time. Role roots are named factory.author/review/prepare and close with their actual error
status. Raw exception capture, prompts, code, tool arguments/results and hidden reasoning remain
excluded. The collector preserves only the new bounded fields in both trace/log filters.
This does not invent per-request visibility or treat provider costs as bank invoices.

A real local ingestion/readback canary passed: trace`1d29b8c83137834de9a069e4301864db`,
ERROR/CLI_STARTUP_FAILED, startup phase, exit1, zero requests, known zero cost,1250ms actual duration.
Deliberately injected synthetic content was removed and root I/O stayed empty. This is a
synthetic privacy/diagnostic mechanism check, not a successful product build. Private proof:
`demo/.local/upgrades/langfuse-diagnostics-20261105/latest.json`.

## Cockpit and remaining implementation

The interface now preserves expanded build evidence and keyboard focus during poll/SSE refresh,
does not replace unchanged lists, exposes the full build session and external product check
diagnostics, and moves successful results for older MD contracts into historical attempts.
The19 client checks pass. Current full engine regression passed694 tests; later focused receipt
checks also passed. These counts do not replace actual main/product/browser verification.

PostgreSQL/React draft helpers still need complete trusted integration and real worker-produced
product changes. Compile the production package before candidate unit tests; isolate test and
graded database/workspaces; freeze dependency bytes; verify migrations/import/restore/roles and
production React/browser behavior. A fixed-upstream product proxy has passed synthetic real-HTTP
cookie canaries but is not yet wired into deployment. Separate localhost ports do not isolate
browser cookies. A real demo must sit behind the trusted cookie-filtering proxy.

Native admission freshness must also be rechecked dynamically, with truthful progress and safe
automatic requalification rather than a permanently cached startup decision. Actual protected
publication, verified product deployment and final browser acceptance remain necessary before Go.
