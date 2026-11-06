# Changelog

## Unreleased

- Update the Æion Factory template from v2.1.0 to v2.1.1 so Grok loads the shared guards from
  `.grok/hooks/factory.json`. The 250k/300k size is `signals.json` `contextTokensUsed`; the Claude
  budget hook does not latch when Grok loads `.claude/settings.json`. The project's stricter git
  transport guard stays.
- Give one feature launch up to three author attempts on different models, each with up to two
  correction rounds by its own model; a crashed author's validated files carry to the next attempt
  with its crash code and error class. Every factory agent receives the same pipeline context and
  leaves owner-only feedback in the receipt. Workspaces of terminal builds are removed after seven
  days, and a failed build's branch is deleted once its pull request was closed unmerged.

- Count each model at its measured Go allowance multiple (Haiku and Luna 4x the list price), bound an
  appended turn by the previous reported input plus its new messages instead of the whole byte bound,
  skip a model whose single request exceeds half of its purpose's cap, and raise the author cap to 5 USD.
- Update the Æion Factory template from v2.0.3 to v2.1.0 (build skill, template-update tool, engineering
  and owner-preference policies, ub-mode credit); the project keeps its stricter git transport guard.
- Rewrite the README around the repository's three parts: framework, offline examples, local factory pilot.
- Turn a reviewer rejection or a failed final gate into at most two automatic correction rounds:
  the next author starts from the exact refused candidate with the reasons as bounded untrusted
  data, and faces the full gate and two new votes; an unchanged correction or a third refusal
  waits for the owner. Authors are told their OpenShell sandbox is not the product runtime and
  must not change ports, routes or defaults the brief does not ask for.
- Update OpenShell from 0.1.5 to 0.1.7 (binaries, Python SDK, sandbox and supervisor images by
  digest); the existing mTLS client CA satisfies the gateway authentication now required.
- Add GPT-6 Luna (OpenCode Go) and Mistral Large 4 (OpenCode pay-as-you-go balance) as factory
  authors and reviewers at their native maximum effort (`max` and `high`), enforced by the relay.
- Settle each forwarded request on the provider's reported input count, with cache reads at the
  cache-read rate, so a Qwen or Haiku author is no longer stopped for budget on an admission byte
  bound about eight times its real input (build ea3fe718: BUDGET_STOP at 0.155 USD of 2 USD).
- Run every agent at its model's maximum reasoning effort (GLM, DeepSeek, Haiku and Qwen; never
  medium), with the relay enforcing it. The author may run protected checks as often as its window
  allows, may not stop while its last check failed (up to three reminders naming the failing
  tests), and is told not to start Gradle or other builds in the offline sandbox shell.
- Keep a busy model provider from holding a passed build: the relay retries HTTP 429/5xx twice
  (honouring a short `Retry-After`), names what remains `PROVIDER_RATE_LIMITED` or
  `PROVIDER_UNAVAILABLE`, and a review vote that produced nothing goes once to the next eligible
  independent reviewer. The cockpit shows each vote with its provider HTTP status, the replaced
  reviewer, and the one-time operator retry instead of advising a full relaunch.
- Make the author agent's time window configurable in `demo/budget.conf`
  (`AUTHOR_TIMEOUT_MINUTES`, 5 to 180 minutes, default 30; the shipped file sets 180). The worker
  lease grows with it and `AUTHOR_MAX_USD` still stops spending first.
- Show stalls in the cockpit: while the author runs, its card shows elapsed time against the window,
  time since the last tool or model step and failed draft self-tests, with a warning after ten silent
  minutes or three failed drafts.
- Give a relaunched author the previous protected-check refusal of the same spec (reason, failing
  test names, compiler locations) as bounded data, so it starts with the test that failed last time.
- Add a dark mode to the cockpit and the lab: every colour comes from `demo/app/theme.css`
  (light and dark sets) with an Auto/Light/Dark toggle. Rebuild `/lab` as a showcase for
  engineers (idea, architecture diagram, each stack piece and how it connects, circuit) that keeps
  the playground, and make its memory room functional: read back this observer's claude-mem
  checkpoints with a hash match, and ask Hindsight a bounded question.
- Label the agent's in-session check as "Agent self-test (draft)" until the protected gate runs,
  so an intermediate draft failure no longer reads as the build's final check.
- Stop the controller's child processes from crashing on macOS ("Python quit unexpectedly"):
  gRPC, loaded by the OpenShell client, restarted its threads in every forked child before exec.
  The controller and OpenShell qualifier now disable gRPC fork support before importing it.
- Simplify the cockpit: a "Your next step" banner with one plain owner action, then factory
  mode, today's budget and environments (Staging/Production "Not deployed yet" until a real
  deployment exists). Remove the synthetic canary drill from the cockpit, explain review holds in
  plain words, and label the model lab as an advanced page not needed to build features.
- Require reviewers to submit their verdict through the typed tool: a Flue finish hook asks once
  when a session ends without it. Failed votes keep their failure code and metadata, and one
  explicit operator retry reruns gates and both votes after a hold with no rejection.
- Make spending bounds owner-configurable in `demo/budget.conf`: daily purse (at most $15), one
  author execution (at most $5, default $2) and one review vote (at most $1). Invalid values hold
  builds and admit no spending.
- Let the relay wait up to 300s for a silent reasoning provider instead of cutting it at 45s,
  and report a stall as `PROVIDER_TIMEOUT` rather than a generic transport error.
- Review incremental changes against their exact frozen Git base, with complete file coverage.
  Allow one fenced, known-cost old-envelope reassessment with fresh checks/votes and preserved
  rejection history. Label the historical canary preview as synthetic instead of product staging.
- Wire separate PostgreSQL unit fixtures, fixed import/restore oracles and frozen React tools.
  Prepare a maintainer-only CI update without giving workers control of their checker programs.
  Keep validated, fully accounted stopped candidates subject to external checks and both reviews;
  allow a bounded30-minute author window and prevent slow trace export from blocking accounting.
- Adopt Factory2.0.3 while preserving protected team mode. Upgrade Langfuse to pinned4.75.0
  after verified cold backups and preserve bounded effort metadata through the collector.
- Refuse Git transport program overrides and explicit remote-helper URLs in the shared
  Bash guard, including abbreviated options and nested shell commands.
- Separate native factory admission from product delivery; isolate external acceptance from
  the candidate process, bind dependency publication to frozen bytes, reject nested Git
  control files and provide frozen acceptance to workers. Align100MD documentation scopes.
- Bind YAML-prefixed MDs correctly at CLI startup, honor factory request bounds, preserve
  validated partial exports on failure and recheck live admission without consuming queued work.
  Separate production packaging from candidate tests and persist routing cohorts with execution bounds.
- Expose real failure status, cause, duration and bounded usage in Langfuse; retain expanded
  cockpit evidence and visible implementation stages. Extend source-backed architecture coverage
  to the actual cockpit/worker/checker/publication runtime and correct obsolete product instructions.
- Run startup-refusal probes before the main app occupies their loopback port, avoid false
  disclosure matches on short numbers and preserve the last checker cause after interruption.
  Refuse changed-source qualification for a stale loaded runtime; isolate old checker outcomes.

- Let Qwen/Haiku launch complete bounded inputs without treating a byte cost estimate as an
  exact context count. Gate continuation on measured API usage including cache; retain budgets,
  unknown-usage stops and isolation. Check bootstrap documentation against the actual PR diff.
  Refresh protected product main through an isolated read-key process before freezing a task,
  preserving local HEAD and operator edits and refusing rewritten or concurrently changed refs.
  Materialize that exact main from shallow checkouts even when it exists only as a remote ref,
  keeping operator edits intact and removing incomplete clones on fetch failure. Refuse candidate
  JUnit extensions, service providers, platform properties, foreign packages and skipped or
  unreported contract XML results in the protected check and artifact gates, after reproducing
  and blocking an `InvocationInterceptor` bypass against exact product `main`. Map Antigravity
  `read_file`, `write_file`, `edit_file` and `run_command` `toolSummary` in `tools/agents/hook.py`,
  defer `Telemetry` import in `FactorySession` so Docker-free host checks run without the
  OpenTelemetry SDK, collect intermediate sandbox writes during handover preparation, and implement
  seed/collect/sync on LocalSandbox for development verification.

- Enforce explicit DeepSeek reasoning effort and bounded, known-cost recovery for complete
  bootstrap reviews. Keep effort metadata comparable and preserve historical memory documents.
  Refuse completion/publication staging from an expired worker even before restart reconciliation.
  Allow explicit publication recovery from a known effect-free permission refusal only after
  confirming unchanged main, frozen bytes and absence of the remote branch/PR.

- Qualify Chromium with its sandbox enabled and pinned current seccomp rules, isolate disposable
  PostgreSQL administrator/migration/application roles, and require PostgreSQL/React plus real
  protected-main evidence before factory activation. Support complete maintainer bootstrap reviews
  with bounded output and retained known-cost failures; publication remains gated by two approvals.

- Bind factory completion to the current specification, preserve versioned integration history,
  qualify a disposable PostgreSQL check boundary, and distinguish queued/publication activity
  and scripted simulation honestly in the cockpit. Live activation remains pending.

- Replace the direct-call factory engine with Flue/Pi roles, shared automatic Java MD preparation,
  independent baseline assertions, complete acceptance/spec/artifact reviews and persistent measured
  routing. Add durable credential-separated PR/CI/main continuation, generation-checked progress,
  remote-effect reconciliation and precise cockpit blockers/MD preview. Protect evaluator reads and
  cleanup against candidate symlink swaps. Export bounded role outcomes to both memory backends.
  PostgreSQL/React qualification, product bootstrap and real main publication remain gated.

- Regenerate all 100 Agora feature contracts for Quarkus/Java, PostgreSQL and React web.
  Preserve stable IDs, add dependency-first sequence and three bounded delivery steps per MD,
  narrow separate-product write scopes, freeze the shared architecture digest, repair missing
  prerequisites and clarify migration/restore, CSRF, audit, appeals and reply provenance.
  The cockpit displays that sequence; catalog regeneration does not certify runtime migration.

- Connect feature 007 to the canonical product with a pinned target, a protected content
  sanitization contract and isolated operator-path qualification. Give the author bounded
  complete main-Java context from the exact Git commit, reject unsafe/missing/oversized blobs
  and refuse oversized briefs instead of silently truncating them. Completed-feature locks,
  budget gates and independent review remain required.

- Complete the direct feature-017 repair in its canonical product repository and verify the
  exact local commit through the independent external contract before recording a locked
  baseline. Persist baseline proof/trace metadata and replay verification idempotently. Expose
  sanitized compiler diagnostics, accept complete review inputs up to 24000 characters, fix
  macOS workspace aliases, refuse the legacy paid-review-only CLI and use project trace links.

- Serialize build claims and final transitions across processes; size leases for real checks,
  hold interrupted attempts without automatic paid retries, retain held-attempt evidence and
  refuse another launch until a held request is explicitly cancelled. Reject malformed queue
  values with HTTP 400 and emit bounded telemetry on builder failure. Allow 180 seconds for
  authoring while retaining 60-second review transports.

- Resolve validated live targets per selected feature, including the new feature-017 strict-request-validation contract. Persist unexpected worker failures as visible holds, refuse unsupported work before reserving budget, and require the independent review circuit for paid builders.

- Make the operator cockpit the default view, with searchable feature availability, persistent completed/in-progress launch locks, recent build evidence, separate simulation history and daily budgets. Keep the scenario lab at `/lab` and load the release drill only on demand.

- Update the harness connectors to Æion Factory **v1.9.3**. The factory added
  `tools/agents/pi-rpc`, the headless Pi RPC runner behind `tools/agents/run pi rpc`, and made it
  part of the connector set; `tools/agents/run` now dispatches `pi rpc` to it and
  `tools/agents/connectors.py` lists it. The factory changed no merge file in this release, so
  `AGENTS.md` and the harness settings keep this project's text. `adapter-check --ref v1.9.3`
  reports 28/28 matching with 0 drifted; the project's `factory-tests`, demo suite, doc-links,
  knowledge-check and repo-health pass. The vendored factory-owned tools also move to the same
  release: `tools/agents/adapter-check`, `tools/agents/template-update` (now with `--from-ref`),
  `tools/factory-tests` and the connector, hook and Pi-RPC tests they run. Project-adapted files
  (`tools/architecture/views.json`, the local `repo-health`) stay untouched.

- Give the demo's product snapshot one owner and a drift check. `demo/forum-app`,
  `demo/forum-db` and `demo/forum-mobile` are byte-identical to `aeion-autonomous-forum` at the
  base commit the feature targets pin; they are now a read-only snapshot named by
  `demo/forum/source.json` and locked per file in `demo/forum/source.lock.json`.
  `demo/forum/source.py --check` fails on a hand edit, a deletion or an extra tracked file, and
  `--refresh --product <checkout>` re-copies the pinned commit (reading the product's object
  store, because the product marks `/demo` export-ignore) after refusing a dirty snapshot. The
  knowledge CI job runs the check, so the snapshot cannot drift silently.

- Reconcile the OpenShell reaper with the factory's build leases. `demo/openshell/reap.py` reads
  `demo/.local/factory/factory.db` read-only and holds the sweep while a dispatched lease is
  still live, or when the store exists but cannot be read: the age window alone could remove a
  long build's sandbox, and an unreadable store is not proof that nothing runs. Containers are
  listed before the lease is read, so a lease claimed in between is seen; an absent store still
  allows the bootstrap sweep because no factory build can exist. `--execute` exits 1 when the
  gate held, and the bootstrap reports only what it removed.

- Make the host-only bootstrap path importable without the model toolchain.
  `token_budget` loads `jinja2` and `tokenizers` only when `TokenBudget` is constructed, the
  runtime counting tests require the pinned wheels before they run, and the runner tolerates a
  host without the OpenTelemetry SDK when marking a failed span. The Docker-free CI job can run
  the teardown and settlement regressions again; the demo venv behavior is unchanged.

- Budget each model review vote as its own paid action. `DispatchWorker` reserves `$0.05`
  from the product purse before every vote and settles only that call's measured usage;
  `LiveReview` keeps the provider usage surface the wrapper needs, the wrapper clears any
  earlier vote's usage before the call so a failure cannot settle stale cost, and a vote with
  unknown usage stays open. A configured review circuit therefore cannot spend two calls against one
  build reservation.

- Give the builder and the operator profiles one eligibility authority. The four
  owner-authorized workers now carry their authorization date and recorded profile expiry in
  `demo/factory/models.py`; `demo/app/profiles.py` asks that catalog instead of keeping a second
  `valid_until`. DeepSeek's harness profile expired on 2026-10-31, so the owner's spend
  authorization on 2026-11-02 does not silently requalify it: the router no longer selects it and
  `complete_with_usage` refuses it before transport, while GLM, Qwen and Haiku stay eligible.

- Run protected candidate checks in a qualified Docker boundary and make paid authoring real.
  `demo/factory/isolation.py` runs the Gradle contract in a disposable non-root container with
  `--network none`, no Docker socket, no host home or controller mount, a fixed environment,
  dropped capabilities and bounded CPU/memory/PIDs; the probe's image digest and denied network
  are recorded with the check, a failed boundary holds `sandbox_unqualified` (the hold reads the
  nested check detail, not a top-level reason), and a contract file altered during the run is
  detected. `demo/factory/live.py` adds the live builder behind the same frozen scopes, canonical
  wire ids from the shared catalog, bounded JSON parsing and provider-reported usage; every `.`,
  `..` or `.git` path component is refused before the scope prefix is trusted, each call resets
  its usage so a failed attempt cannot settle with the previous cost, and unreported cost keeps
  the reservation open. A failed paid builder still names its own author model in the receipt.
  The qualified image digest, not the mutable tag, is what both the probe and the check run, so
  a re-tagged or re-pulled tag cannot execute unqualified bytes; a symlinked parent cannot
  redirect a write outside its matched scope; deleting the contract during a check is
  tampering, not a missing toolchain; a timed-out or interrupted check removes its named
  container; and the probe carries a host sentinel it asserts absent in the container instead
  of forcing it empty.
  A completed paid attempt
  is `live_complete` with `simulated: false`, and only measured complete usage settles its
  reservation. The cockpit shows the trace state, and a backend readback is what turns
  `exported_unconfirmed` into `confirmed`. `demo/factory/baseline.py` records a verified
  pinned-base baseline (hashed paths and an isolated passing base suite), which unblocked 013
  against 001. One real paid build passed the isolated check and was read back from Langfuse.

- Give the operator front one explicit execution path instead of a silent fake fallback.
  `demo/factory/execution.py` resolves `simulator` or `offline`, loads the pinned forum
  profile and the shared deterministic offline builder, and returns a visible
  `execution_unavailable` hold when the profile or product checkout is missing. `FactoryApp`
  forwards those components to its worker, a pinned target now holds `target_feature_mismatch`
  rather than freezing another feature, and the catalog response plus the front badge show the
  mode, the hold and the `live_builder_unqualified` reason. Queuing feature 013 on the live
  store is honestly held at `dependency_missing` until dependency 001 has merged evidence;
  the offline completion was proven with a fixture catalog, not a simulation receipt.

- Update this project and the canonical forum checkout to Æion Factory **v1.9.2** with the
  factory's `template-update`: one contract file changed in each
  (`.pi/extensions/factory/index.js`), and the factory's `adapter-check --ref v1.9.2 --root
  <project>` reports 27/27 connectors matching on both. The adopted checkout has no v1.9.2 tag,
  so the reference is resolved from the factory repository. The 250k decision now happens at settlement with a live context measure
  instead of starting a compaction from a tool result, and a one-shot print run ends by pointing
  at the verified handover. The factory-owned `tools/agents/tests/test_pi.mjs` and `.pi/README.md`
  were refreshed from the same tag so `tools/factory-tests` no longer asserts the 1.9.1
  tool-result compaction. The application `VERSION` stays `1.9.0`; the forum change is local
  commit `ab72692`, not pushed.

- Refuse an incomplete review instead of approving an excerpt. `review_circuit.py` now builds the
  complete changed bytes into one bounded envelope; an oversized input holds with
  `review_input_too_large` before any model is called, an unknown author holds with
  `author_identity_unknown` because its family cannot be excluded, and an approval records
  whole-file coverage plus a content digest. The factory exporter no longer reports a created
  span as `emitted`: it returns `exported_unconfirmed` only when the local transport accepted the
  span, `export_failed` when it refused or raised, and reserves "confirmed" for a Langfuse
  read-back. The daily budget day is explicit `Europe/Paris`, not the host's local zone.

- Reap orphaned OpenShell containers instead of letting them burn CPU forever. Nine
  supervisor/sandbox pairs from an interrupted 2026-11-01 qualification were still running 14
  hours later (each supervisor used 5–22% CPU); the gateway had no records for them.
  All 18 labeled containers were removed. `demo/openshell/reap.py` now selects only
  OpenShell-labeled sandbox containers older than a 3,600-second safety window, dry-run by
  default and `--execute` to remove; bootstrap runs the same sweep before qualification. The
  reaper is covered by `demo/tests/test_openshell_reap.py`.
- Move the runnable forum to the separate
  [`aeion-autonomous-forum`](https://github.com/OualidGuennif/aeion-autonomous-forum) checkout as
  the canonical product source, because autonomous workers only hold a GitHub key there.
  `demo/forum/targets/forum-app-013.json` now names that repository, its import commit
  `37417ab`, the Quarkus main/test scopes, an adapted brief and an external protected Gradle
  check; `DispatchWorker` clones the product checkout, and the qualification passed from it
  (build `311a5ac3…`, 28.3 s, trace `94563192…`, Langfuse readback PASS). The product repo also
  carries commit `1224d03`, which publishes the offline-qualified feature-013 header filter, and
  `4e27f73`, the local Docker packaging. The container was verified healthy on
  `127.0.0.1:8081`, with CSP, `nosniff`, `no-referrer` and HSTS on `/healthz` and on a 404, and
  no report-only header. No paid inference, registry push, VPS deployment or remote publication
  ran. The main repository's `demo/forum-app/` is now a reading mirror.
- Enforce two independent daily purses of **$15.00**: `aeion-observability` for the cockpit and
  `aeion-autonomous-forum` for the factory workers. `demo/factory/budget.py` journals a
  reservation before any live work and settles the actual cost after it; an open reservation
  counts against the day, a corrupt ledger fails closed, one purse cannot borrow from the other,
  the cockpit stops a live run with `BUDGET_STOP` and a worker holds `budget_unavailable`.
  `FactoryApp` and the cockpit `Runner` share one journal and pass their own scope. The paid
  publish worker now holds its own forum purse and reserves a positive $0.10 before it can call a
  reviewer; an entry point without a purse holds `budget_unavailable` instead of spending freely.
  No paid inference was authorised or run.
- Confine the protected check to the worker's materialised tree, so a manifest or forged verdict
  cannot point it at the controller or another host directory. A verified publish receipt now also
  requires at least two approved votes from distinct model families, not just two vote objects.
- Remove the obsolete Deno/Hono demo: `demo/playground/` and its Compose service, cockpit
  integration dot, hero link, `Runner.probe` and the Deno-span read-back are gone; `/factory`
  is the operator entry and the forum is the only product demonstration. The cockpit links the
  forum API and web front, and `demo/tests/test_playground_removed.py` keeps the old surface
  from returning.
- Bind publication to the reviewed bytes. The artifact digest now covers each path and its
  content; renames, deletions, binary blobs and unreadable files are held as unsupported effects
  instead of being silently dropped. `verified_receipt` and `Publisher.decide` recompute the
  digest and refuse a request whose bytes, path set or review digest differ from the approved
  artifact. `load_publish_credential` imports `for_role` (the reproduced `NameError` is gone), the
  review circuit records `approved`/`rejected` so two valid votes score 1.0, and the readiness
  diagnostic talks to the sandbox helper instead of importing the server that serves on import.
  The release proxy is explicitly read-only: non-GET requests get 405, and authenticated requests
  are refused with 400 before the cache. Covered by new and updated tests in
  `demo/tests/test_factory_{publish,pipeline,s3,review_circuit,publisher_credential}.py`,
  `test_deploy_playground.py` and `test_live_readiness.py`.
- Confirm the Æion Factory v1.9.1 template: `template-update --from-ref v1.9.0 --ref v1.9.1`
  reports no contract file differing and `adapter-check --ref v1.9.1` matches all 27 connectors;
  the four readers changed in v1.9.1 were already adopted in `10ded60`. The demo's product
  checkout under `demo/.local/factory/agents/aeion-autonomous-forum` was moved from v1.8.6 to
  v1.9.1 the same way (five contract files, `adapter-check` PASS).
- Run the forum's React Native front in a browser through `react-native-web`
  (`npx expo start --port 8082`): the API allows exactly `http://127.0.0.1:8082` and
  `http://localhost:8082` with credentials, `src/api.ts` lets the browser's cookie jar own the session
  (`credentials: 'include'`) while still reading the CSRF token from the login body, and the iOS path
  keeps typechecking, bundling and passing its 12-step smoke test. `python3 demo/setup.py` now writes
  `LANGFUSE_EMAIL` next to `LANGFUSE_PASSWORD` in `demo/.local/stack.env`, and the compose file reads
  it with a default.
- Update to the Æion Factory v1.9.0 template (tag `v1.9.0`): the 250k latch lets go on a verified
  handover and compacts a stale one; `adapter-check` matches all 27 connectors; five tool files a
  release behind are refreshed from the tag, which is what makes `tools/factory-tests` pass again.
  `tools/architecture/views.json` regains the three views `refresh` requires — this repository's
  overview, now citing a verified source anchor for each of its twelve components, plus the release's
  delivery and context views — and `demo/tests/test_sandbox.py` proves the sandbox refusal with an
  inert stub instead of depending on the OpenShell SDK being importable.
- Update to the Æion Factory v1.8.4 template (tag `v1.8.4`, commit `fac8bcb`): the dsh web plugin
  tells the shared 250k/300k rule that its profile has no compaction service, so the gate is
  advisory and the harness compacts itself instead of asking for `/compact`; Pi's native compaction
  runs and owes its receipt; `adapter-check` reports a `steer` call without an id as `UNIDENTIFIED`;
  `tools/agents/{connectors.py,refs.py,dsh-install,template-update}` and the `template-update`
  skill arrive, and `tools/factory-tests` runs their suites.
- Adopt the Æion Factory v1.8.3 template (tag `v1.8.3`, commit `bac6d7b`): `tools/`, `efficiency/`,
  native harness folders, `VERSION`, knowledge policies, merged `AGENTS.md`, the agent adapter check
  and the prompt-defense hook, and the Factory knowledge docs the imported tools name as their spec.
- Verify Pi-to-Langfuse transmission end to end on the local stack, with a local fake model and no
  paid call; the record and the Langfuse v4 read path are in `work/langfuse-pi-plugin.md`.
- Add the fleet view to the cockpit: every run, every tier, one glance, linked to Langfuse.
- Add the high-level architecture diagram (`docs/architecture/`), built with Graphify and Archify,
  and point the committed `tools/architecture/views.json` at this repository's own view.
- Split the specification in two: `demo/forum/PLAN.md` is the product (Agora and its 100 app-only
  features), `demo/forum/ECOSYSTEM.md` is the factory that builds it (board, queue, dispatch,
  gates, merge allowlist, observer agent). The 14 factory features that were numbered inside the
  100 are replaced by 14 product features, and the review bundle carries both files.
- Specify Agora, the agent forum, and the build plane that will produce it: `demo/forum/PLAN.md`
  and 100 feature files with a generated manifest and index, plus a verbatim review copy under
  `demo/forum/openAI/`. Specification only; no forum code exists yet.
- Import the Factory `loops/` jobs (orchestrator, prompts, schedules, model routing, Decisions API
  client) that `tools/loops`, `knowledge/operations/loops.md` and `.github/workflows/outer-loop.yml`
  already named, so `tools/factory-tests` passes to the end; ignore `env.local` as Factory does.
- Fix two macOS-only test expectations (a `/private` temporary path and a framework interpreter that
  rewrites `argv[0]`).
