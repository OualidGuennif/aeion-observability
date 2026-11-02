# Changelog

## Unreleased

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
  redirect a write outside its matched scope; and deleting the contract during a check is
  tampering, not a missing toolchain.
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
