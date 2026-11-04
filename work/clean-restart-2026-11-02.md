# Local clean restart and actual readiness — 2026-11-02

Owner request: reload and restart the local stack cleanly, then verify whether new features can
be launched from the cockpit. The restart preserves data, history, budgets and credentials;
it is not a reset, model evaluation, remote publication or deployment.

## Running services

All nine `aeion-observability-demo` containers were stopped gracefully and restarted through
the existing Compose configuration, with `--no-build --pull never --wait`. Existing private
configuration was consumed by the trusted runtime, without inspection or regeneration.
PostgreSQL, ClickHouse, Redis, MinIO and Langfuse Web report healthy. OTel, Langfuse, Hindsight
and claude-mem return HTTP 200 and the controller reports all four integrations connected.

The canonical product commit is `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`. It was materialized
into a disposable exact-commit clone and packaged offline through the qualified Docker runner
(network denied, non-root, read-only root/cache/toolchain, no host credentials or Docker socket).
Both Gradle packaging and the local runtime image build returned 0. Only the resulting public
Quarkus application and the canonical Dockerfile's runtime stage entered the image context;
the controller/private product checkout did not. No dependency versions changed or images
were pushed. This packaging step does not claim a new test execution; the exact-commit tests
are recorded in the [repair evidence](feature-017-codex-repair-2026-11-02.md).

| Runtime evidence | Value |
| --- | --- |
| Running product image | `sha256:b8492267d6c5e1783b37ac16c30167dd5e902a3cc55b43ce36b0393fe4e29075` |
| Retained rollback image | `aeion-autonomous-forum:before-017-restart` |
| Preserved forum data volume | `aeion-autonomous-forum_forum-data` |
| Forum API | `http://127.0.0.1:8081/healthz`, HTTP 200 |
| Canonical product web front | `http://127.0.0.1:8082/`, HTTP 200 |
| Web JavaScript bundle | HTTP 200, 1754456 bytes |
| Factory cockpit | `http://127.0.0.1:8088/`, HTTP 200, live mode requested |
| Langfuse | `http://127.0.0.1:3300/`, public health HTTP 200 |
| Native OpenShell gateway | `127.0.0.1:17670`, mTLS health version `0.1.5` |

The forum container was recreated with the new image and the same named data volume. A fresh
ephemeral session secret was generated internally, so prior forum sessions must sign in again.
No account, message, database volume or session secret was read or printed.

The Expo front now runs from the separate canonical product checkout, using a local copy of
the already-installed dependencies after byte-identical lockfile verification. No new package
was downloaded. Its launcher uses `--web --localhost --port 8082 --clear`, disables telemetry and
dotenv loading, and explicitly points the public API URL at loopback. Actual host listeners on
8082, 8088 and 17670 are restricted to `127.0.0.1`. The API accepts exactly the front's origin
with credentialed CORS. Anonymous access to the factory catalog still returns HTTP 401.

## State and behavioral checks

Before stopping the controller, an atomic SQLite preflight found no queued/dispatched build;
the lab also had no running scenario or campaign. The exact old native process identities
were verified before graceful termination. Other projects and interactive harnesses were not
stopped. No volumes were deleted and no container/image prune was performed.

Live API checks of feature 017 pass: an empty login object returns 422 with only the missing
field paths, and null/unknown fields return 422 with the expected paths and feature-013 response
headers. A body above 16 KiB returns 413. The global Quarkus body cap can refuse before JAX-RS,
so that 413 is not claimed to use the filter's JSON error envelope.

The before/after budget ledger SHA-256 is identical. Both scopes retain $1.00 counted and
$14.00 remaining from a $15.00 daily cap, including prior unknown-usage liabilities. Build row
count and idle queue state are unchanged. No paid model call ran during packaging or restart.
Feature-017 baseline `2716fe2bb1044ceabdecdcc6f4e38513` is still implemented and locked, and
Langfuse backend readback reconfirms trace `18fe0c7e99f4af1cb8d78278cf42d7f9`, observation
`9951e9bf4653582e`.

## Can a new feature be launched now?

No: current persisted availability has **0 selectable features**, with 001, 013 and 017
completed. The live resolver successfully loads targets 013 and 017 without an execution hold,
but both are already locked. The other 97 planned catalog entries need their real execution
contracts and prerequisites. Restarting services cannot manufacture those contracts or justify
unlocking completed work. The next implementation work is to connect a genuine next feature,
not to enable unsupported checkboxes.

The model catalog currently allows GLM, Qwen and Haiku; DeepSeek remains excluded by its expired
profile. This is routing eligibility, not a new model-quality evaluation or paid transport test.

The separate advanced Flue lab still reports `live_ready=false` and `sandbox_ready=false`.
A healthy OpenShell gateway is not proof that its sandbox transport is qualified. The product
packaging used the independently qualified Docker check boundary instead. Authenticated browser
acceptance and automatic tab reload remain unavailable because the browser connector cannot
attach to the existing tab; HTML/bundle/API checks do not replace visual acceptance.

Local operation evidence: `/private/tmp/aeion-cockpit-ui-work/restart-proof.json`,
`runtime-package.json` and scoped helper scripts. No credentials or raw provider payloads are
part of those evidence outputs.

Later owner-authorized work connected [target 007](feature-007-cockpit-wiring-2026-11-02.md).
That activation supersedes this restart's zero-ready snapshot; 007 is now selectable, with the
three completed features still locked and no paid build automatically launched.
