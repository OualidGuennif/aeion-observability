# Changelog

## Unreleased

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
  `FactoryApp` and the cockpit `Runner` share one journal and pass their own scope. No paid
  inference was authorised or run.
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
