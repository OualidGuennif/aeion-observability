# Agora design correction validation — 2026-11-01

Status: **documentation/catalog correction complete; execution awaiting_owner_github_confirmation**.
Base reviewed: `d6500a336ea11adb699fabe1a9be0029d47dd6f3`. Changes are local and uncommitted.
Owner scope: update plans/specs and prepare the DeepSeek handoff under `demo/` only.

## Delivered

- Product/factory trust boundary and future product output root are explicit.
- All 100 Markdown contracts now have eight spec sections and declared phase, builder tier 3,
  dependencies and literal write scopes. IDs and feature filenames remain stable.
- Canonical Python definitions, schema-version-2 manifest, index and review snapshots agree.
  Snapshot relative links are rebased; the generator checks drift in both review files.
- Dependency order separates storage from admission, moves foundational controls earlier and
  removes later-phase prerequisites. The phase and area tables each partition all 100 IDs once.
- 077, 082 and 086 have disjoint output scopes and permit parallel scheduling; other features
  remain exclusive. Runtime concurrency still requires explicit scheduler qualification.
- Content representation, human/agent rights, three-category corpus, quotas, citations, snapshots
  and exports have consistent acceptance contracts. The ten weak criteria from review are revised.
- Protected evaluator/reviewer identity, exact-artifact publication, credential mediation,
  cancellation, replay, crash recovery, bounded cost and restore proofs are specified.
- DEEPSEEK_HANDOFF.md defines the local continuation, blocked until the owner explicitly confirms
  GitHub credential setup. This applies even to S1 and fake runs; waking or detecting a key is
  insufficient. The OpenCode key is believed configured by the owner, but was not inspected or verified.

## Checks actually run

| Check | Result |
| --- | --- |
| `python3 -B demo/forum/tools/generate_features.py --check` | PASS: 100 features, manifest, index and both generated review snapshots |
| `python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v` | PASS: 15 catalog regressions, including valid forward references, real cycles, phase violations, escape scopes, category mismatch, protected prerequisites and rebased links |
| `PYTHONDONTWRITEBYTECODE=1 tools/knowledge/knowledge-check` | PASS: 0 problems |
| `PYTHONDONTWRITEBYTECODE=1 tools/knowledge/doc-links` | PASS: 93 native contract links |
| `PYTHONDONTWRITEBYTECODE=1 tools/repo-health/repo-health` | PASS: 9 top-level folders, no oversized source or long comment blocks |
| `git diff --check` | PASS |
| Independent local graph/table/link/scope inspection | PASS: DAG with 100 vertices / 311 edges; 123 local Markdown targets resolved; all changed/new files under demo/ |

The independent inspection used a temporary standard-library script, not the generator's
validation function: parsed the JSON graph, expanded the plan's ID ranges, compared each
phase/area assignment, resolved relative Markdown links and enumerated modified/untracked paths.
Phase counts: P0=20, P1=24, P2=16, P3=16, P4=12, P5=12. Scope: 115 modified and 3 new files.

## Evidence limits and pending work

These checks prove catalog consistency and regression behavior of the generator. They do not
prove runtime confinement, moderation effectiveness, privacy, backend ingestion, actual model
quality, production security or autonomous delivery. The protected acceptance scenarios in
PLAN/ECOSYSTEM are requirements to implement, not passing runtime test receipts.

A manual design-boundary assessment covered builder/host separation, gate replacement, receipt
identity, publisher rights and cancellation/recovery. No native security scanner was run and no
runtime security certification is claimed. No agent/model run, paid call, credentials inspection,
remote operation or deployment was performed for this update.

Live operation remains gated by the expired DeepSeek profile, real macOS/Linux confinement
qualification, protected acceptance implementation and separately authorized remote CI/branch
preparation. S4 forum-data restoration waits for an actual product schema; a generic fixture
restore alone cannot qualify that deployment.

Root work/current.md, CHANGELOG.md and knowledge policies were not edited because the owner
restricted writes to demo/. Their historical S1 state is superseded for this continuation by
the local handoff; root housekeeping is explicitly deferred, not silently considered complete.

## Owner startup-hold clarification — 2026-11-01

Added an explicit initial hold to the handoff, both canonical plans, review bundle and demo
entrypoint. DeepSeek must wait for the owner's GitHub-setup confirmation before implementation
or any fake/local run. OpenCode credential presence remains unverified; no secret file was read.
Rechecked: generation/snapshot synchronization PASS, all 15 catalog tests PASS, doc-links PASS
(93 links), diff whitespace PASS, and startup-hold/scope assertions PASS. These checks validate
the instructions, not a running enforcement mechanism; the factory remains unimplemented.

## START GATE lifted — 2026-11-01 (Europe/Paris)

The owner confirmed in chat that the GitHub credential is placed in the intended host `.env`.
Owner-chosen variable names: `GH_API_KEY` (GitHub — publisher loader not implemented yet, wired
in S3) and `OPENCODE_API_KEY` (OpenCode inference relay). Owner messages: "done c'est fait" then
the naming message, received 2026-11-01 Europe/Paris. No key value was read, displayed or copied;
presence was not independently inspected. The hold is lifted only for the local fake-inference
continuation (S1–S4). Paid/live inference, remote push/PR/merge and deployment stay disabled.

## S1 delivered — local factory board with honest fake execution — 2026-11-01

Status: **S1 implemented; S2 next**. All new code and state under `demo/`; nothing committed.

Delivered (handoff S1 contract):
- `demo/factory/manifest.py` — schema-v2 catalog loader/validator: 100-feature count, per-feature
  fields, tier 3, literal write scopes, unique ids, dependency graph (real cycles and
  later-phase prerequisites rejected), stable order-independent catalog digest.
- `demo/factory/store.py` — supervisor-owned SQLite (WAL) under `demo/.local/factory/`: ten
  nonterminal-build cap, idempotency-key replay/conflict, dependency holds, atomic claim/event
  transitions, exclusive concurrency 1 plus disjoint `parallel` scheduling, cancellation
  generation, late-result rejection, expired-lease reconciliation on restart.
- `demo/factory/auth.py` — administrator sessions (bootstrap token rotated on login, idle +
  absolute expiry, constant-time compare) and loopback Host/Origin checks.
- `demo/factory/worker.py` + `demo/factory/sse.py` — fake worker with disposable simulated diff
  receipt (`simulated_complete`), bounded SSE hub with reconnect cursors.
- `demo/factory/api.py` — HTTP trust boundary: login, catalog, board, queue, cancel, logout, SSE;
  every read requires a session, every mutation also requires CSRF + Host/Origin + JSON body limits.
- `demo/app/` routing integration (small): `/factory`, `/factory.js`, `/factory.css`,
  `/api/factory/*` in `server.py`, plus `FACTORY_STATE`/`FACTORY_MANIFEST` in `settings.py`.
  Board UI (`factory.html/js/css`) reuses the cockpit ivory/forest/copper styling.

Checks actually run (system python3 3.15 and the demo venv):
| Check | Result |
| --- | --- |
| 52 new factory tests (`demo/tests/test_factory_{manifest,store,auth,worker,api}.py`) | PASS |
| Full `demo/tests` suite (venv) | 92 tests, 1 pre-existing env error: `test_openshell_setup` `ps` denied by the macOS sandbox (unrelated to this change) |
| End-to-end HTTP smoke (`server.py` on :8099, temp state) | PASS: login→csrf, catalog 100, queue 001 admitted, queue 002 held `dependency_missing`, mutation without CSRF 403, tick → `simulated_complete` |
| `python3 -B demo/forum/tools/generate_features.py --check` | PASS |
| `tools/knowledge/knowledge-check` | PASS (0 problems) |
| `tools/knowledge/doc-links` | PASS (97 links) |
| `tools/repo-health/repo-health` | PASS |
| `git diff --check` | PASS |

S1 proves: ten-item cap, replay/conflict, missing prerequisites, exclusive/disjoint scheduling,
malformed-catalog refusal, wrong/missing/expired/cross-origin session refusals, CSRF refusals,
cancel-before/after work, and restart without duplicate claims — all against the fake worker.

S1 does **not** prove: real tier-3 containment, protected gates, forge operations, or anything
paid/remote. Dependencies stay held because only a real merge (S3) satisfies them; the real
catalog is never marked merged here. S2 is next (frozen dispatch + real containment, still fake
inference), followed by S3 and S4.

## S2 delivered — frozen dispatch and artifact validation (still fake inference) — 2026-11-01

Status: **S2 local part implemented; real tier-3 containment still blocked on macOS**. Nothing
committed; all new code and state under `demo/`.

Delivered (the part implementable without the macOS transport):
- `demo/factory/freeze.py` — `FrozenBuild` binds build_id, feature id, manifest digest, spec
  digest (the feature Markdown file), base SHA, literal write scopes, tier, parallel flag,
  dependencies and configured bounds (deadline, step cap, context limit, cost reservation).
  Missing spec or bound raises `FreezeError` → the build is held, never invented by the builder.
- `demo/factory/artifact.py` — enumerates the actual Git diff (`git diff --name-status` +
  untracked), validates every changed path (renames at both endpoints) against the frozen literal
  scopes, and rejects traversal/absolute paths, symlinks, `.git` metadata, non-regular entries and
  out-of-scope paths. A mixed diff is rejected as a whole.
- `demo/factory/dispatch.py` — `DispatchWorker` freezes the build, runs the fake builder in a
  disposable Git repo, validates the diff, then completes `simulated_complete` with a PR-shaped
  (explicitly `simulated`) receipt carrying `frozen_digest`, `base_sha`, `artifact_digest` and the
  allowed path list; an unsafe diff completes `failed`.
- `demo/factory/store.py` — added `hold_dispatched` for a build whose freeze fails.
- `demo/app/` wiring: the live board now uses `DispatchWorker` (`spec_dir`, `S2_CONFIG` bounds).

Checks actually run:
| Check | Result |
| --- | --- |
| 12 new S2 tests (`test_factory_s2.py`, `test_factory_dispatch.py`) | PASS |
| Full `demo/tests` suite (venv) | 104 tests, 1 pre-existing env error (`test_openshell_setup` `ps` denied) |
| End-to-end HTTP smoke (S2 worker) | PASS: queue 001 → `simulated_complete` with `frozen_digest` + `base_sha` + `artifact_digest` + `allowed` |
| `generate_features.py --check`, `knowledge-check`, `doc-links` (97), `repo-health`, `git diff --check` | PASS |

S2 **does not** yet prove: real tier-3 confinement. The approved macOS stdin-copy transport is
still unqualified (host-backed work volume returns `EACCES`, handoff §6), so live mode stays
blocked; a mocked adapter is never relabelled as a security qualification. The participant /
moderator broker interface (product 066) and real GitHub publisher remain for S3.

## S3 delivered — protected checks, publisher policy and observer (fake forge) — 2026-11-01

Status: **S3 local part implemented; the real GitHub publisher is not wired**. Nothing committed;
all new code and state under `demo/`. No remote call, no token read and no PR was made.

Delivered:
- `demo/factory/checks.py` — `ProtectedChecks` registry, held outside any candidate's control.
  `evaluate`/`verdict` return `passed`, `failed`, or **`qualification_missing` when a required
  check is absent** (fail closed, never green by default). `bundle_digest` identifies the approved
  check revision. Defaults: `scope` (the artifact diff was accepted) and `spec_unchanged` (the
  reported spec digest equals the frozen one).
- `demo/factory/publish.py` — publisher policy plus `FakeForge` (in-memory, explicitly simulated).
  Refusals: forged issuer, forbidden target repo, cancelled build, forged receipt digest,
  out-of-scope path. Holds: stale base/head, sensitive path → owner review. The forge can be told
  to return an **uncertain** result; the publisher then reconciles against the forge and never
  blindly re-publishes.
- `demo/factory/observer.py` — bounded, deduplicated observation of completed builds. Each
  proposal carries only identity, status, artifact digest and timestamp (no receipt body, no
  spec text) and is persisted through the `meta` table, so a restart never re-proposes a build.
  `max_batch` bounds a single pass.
- `demo/factory/store.py` — added `meta_get`/`meta_set` (durable, key/value, used only for
  observer dedup markers).
- `demo/factory/dispatch.py` — the S2 worker now gates before recording: freeze → build →
  validate the actual diff → **protected checks** → **publisher policy (fake forge)** →
  `simulated_complete` with the gate verdict and forge decision in the receipt. A missing check
  holds `qualification_missing`; a failed check or a refused publisher decision completes
  `failed`; an owner-review/sensitive or stale decision holds (`owner_review_required`,
  `reconciliation_needed`). The builder now writes inside its first declared write scope, so a
  sensitive scope is genuinely exercised.
- `demo/factory/api.py` — the board tick runs the worker and then proposes each completed build
  once (`observed` SSE event).
- Tests: `test_factory_checks.py`, `test_factory_publish.py`, `test_factory_observer.py`,
  `test_factory_s3.py`, plus an API wiring test.

Checks actually run (demo venv, Python 3.15):
| Check | Result |
| --- | --- |
| 92 factory tests (`test_factory_*.py`) | PASS |
| Full `demo/tests` suite | 132 tests, 1 pre-existing env error (`test_openshell_setup`: `ps` denied by the macOS sandbox, unrelated to this change) |
| End-to-end HTTP smoke (:8097, temp state) | PASS: login → queue 001 → tick → `simulated_complete` with `gate.status=passed` (`scope`, `spec_unchanged`), `publisher.decision=published`, simulated PR receipt |
| `git diff --check` | PASS |
| `generate_features.py --check`, `knowledge-check`, `doc-links`, `repo-health` | PASS |

S3 proves, against a fake forge only: a candidate cannot supply the checks that judge it, a
missing check fails closed, out-of-scope or mixed diffs never publish, sensitive paths stop for
owner review, a forged issuer/target/receipt is refused, and an uncertain forge result is
reconciled instead of duplicated.

S3 **does not** prove: a real GitHub publisher, real branch/PR/merge effects, real tier-3
containment, or paid model quality. `GH_API_KEY` is **not** loaded or used: the GitHub App /
fine-grained-token publisher (Contents, Pull requests and Issues write; Actions read) is still
to be implemented and stays owner-gated. S4 (local VPS runbook and a disposable
SQLite/Postgres restore drill) is next.

## S4 delivered — local VPS runbook and a verified restore drill — 2026-11-01

Status: **S4 local part implemented; product Postgres restore is not covered.** Nothing
committed; every write under `demo/`.

Delivered:
- `demo/factory/runbook.md` — single-process local VPS runbook: what runs (cockpit + factory
  board on loopback), prerequisites, the environment allowlist, a `systemd` unit with a hardened
  sandbox (`ProtectSystem=strict`, `ReadWritePaths` limited to `demo/.local`), start/stop, health,
  a **verified** backup procedure, the restore steps, rollback, the expected hold/failure
  modes, and an explicit list of what it does not qualify.
- `demo/factory/restore.py` — backup through SQLite's online backup API (safe under WAL), then
  `verify_db` re-checks `PRAGMA integrity_check`, the expected schema (`builds`, `events`, `meta`)
  and row counts. Refuses `source_missing`, `not_a_database`, `integrity:…` and
  `missing_tables:…`; a stale destination is replaced, never silently kept. Usable as
  `python -m factory.restore SRC DEST`.
- `demo/tests/test_factory_restore.py` — 5 tests: intact restore into a fresh `Store` (status and
  feature preserved), missing source refused, a non-database file refused, a database without the
  factory schema refused, and a stale destination overwritten.
- `demo/app/factory.js` — the board row now shows a readable receipt summary instead of a raw
  truncation: `gate <status> (check:status…)`, `publisher <decision>`, `fake PR #n`, and the
  `artifact`/`frozen`/`base` digest prefixes; the `observed` SSE event is subscribed.

Checks actually run:
| Check | Result |
| --- | --- |
| 97 factory tests (`test_factory_*.py`) | PASS |
| Full `demo/tests` suite | 137 tests, 1 pre-existing env error (`test_openshell_setup`: `ps` denied by the macOS sandbox, unrelated) |
| Live drill: populated store → backup → verify | PASS: receipt `{"integrity":"ok","builds":1,"events":5,"meta":1,"tables":["builds","events","meta","sqlite_sequence"]}`, restored `Store` readable |
| Live drill on the running board store (`demo/.local/factory/factory.db`) | PASS: `integrity ok`, schema present, exit 0 |
| Final HTTP smoke (:8096, final code) | PASS: `simulated_complete`, `gate passed` (`scope`, `spec_unchanged`), `publisher published`, fake PR #1 |
| `node --check demo/app/factory.js` | PASS |
| `git diff --check` | PASS |
| `generate_features.py --check`, `knowledge-check`, `doc-links`, `repo-health` | PASS |

S4 proves: the factory state store can be backed up while live, the copy is integrity-checked and
schema-checked, a corrupt or partial copy is refused rather than used, and the documented restore
produces a working board store.

S4 **does not** prove: a product Postgres backup/restore (no product schema exists yet), a real
server deployment, real containment, TLS/reverse-proxy hardening, or any remote or paid effect.
The `systemd` unit and the drill were written and exercised locally on macOS; neither was run on
a real VPS in this session.

## Remaining gaps after S1–S4

- The product itself: no forum code, schema or Postgres restore exists yet.
- Root `work/current.md`, `work/validation.md` and `CHANGELOG.md` were not edited because the
  owner restricted writes to `demo/`; the proof lives here in `demo/forum/VALIDATION.md`.

## Containment cause isolated, copy-out transport proven — 2026-11-01

Status: **the macOS `EACCES` blocker is understood and a working transport is proven inside a real
OpenShell sandbox**. The live Flue agent path is **not** yet rewired to it, so tier-3 runtime
qualification is still not claimed.

Cause, measured rather than guessed (recorded earlier in `work/validation.md`, reproduced here):
on Docker Desktop the labeled work volume is a **bind-backed** Docker volume
(`o=bind`, `device=demo/.local/work`). Inside the OpenShell sandbox the write is *performed* — the
file appears on the host — while the syscall returns `EACCES`, for `open(..., "w")` and `echo >`.
`touch` sometimes succeeds. A plain container on the same volume-subpath mount writes normally
(checked: `--mount type=volume,...,volume-subpath=<run>` as uid 10001 → `WRITE_OK`), so the fault
is in the sandbox filesystem path, not in Docker or in the host permissions.

Change: the boundary no longer depends on host-backed writes. `demo/app/sandbox.py` now owns a
sandbox work directory (`SANDBOX_OUT = /tmp/aeion-out`) and collects results **out** over the exec
channel: `collect()` runs a bounded Python collector inside the sandbox and returns
`{relative path: base64}`; `materialize()` writes those bytes to the host while refusing absolute
paths, `..` and backslashes; `Sandbox.sync_out()` composes them. `demo/openshell/qualify.py` now
proves in-sandbox writes, the read-only mount, the invisible sibling directory and the network
denial, then proves the copy-out round-trip on the host, and records `transport: "copy-out"`.

Checks actually run:
| Check | Result |
| --- | --- |
| Real OpenShell qualification on macOS (gateway `0.1.5`, agent image `sha256:4d176896…`, uid 10001) | **PASS**: `uid, filesystem_denied, sandbox_write, workspace_read_only, host_outside_invisible, network_denied` all `true`; `transport: copy-out`; evidence written to `demo/.local/openshell/qualification/security.json` |
| Real sandbox lifecycle: create → exec write → `sync_out` → delete | **PASS**: exec exit 0, `copied: ['workspace/src/agent.txt']`, host bytes `from-sandbox`, sandbox closed |
| `sandbox.connection()` with the new evidence | **PASS**: connects, gateway health `0.1.5` |
| 7 copy-out unit tests (`test_sandbox_transport.py`) | PASS: round-trip, traversal refusal, empty path refusal, failed/unreadable collection, bound |
| Full `demo/tests` suite | 156 tests, 1 pre-existing `ps` denial |

What this does **not** prove, and must not be overclaimed: `runner.live()` still passes the
**host** workspace path to the Flue agent, so the live tier-3 path would still write through the
mounted volume and hit the same `EACCES`. Wiring it means seeding the sandbox workdir, pointing
`AEION_WORKSPACE` at it, and syncing out after the run — and validating that needs a paid model
run, which stays out of bounds. Until then tier 3 remains unqualified at runtime, and the
qualification above certifies the transport, not the agent path.

## GitHub publisher implemented, offline-tested, dry-run by default — 2026-11-01

Status: **implemented and tested against a stub transport; no remote call was made.**

`demo/factory/github.py` adds `GitHubForge`, the real-forge counterpart of `FakeForge`:
- reads `GH_API_KEY` from the environment at call time and never prints, logs or stores it; a
  missing token raises `publisher_unconfigured` before any request;
- idempotent by construction: the branch name is `aeion/build-<attempt_id prefix>`, so an
  uncertain result is **reconciled** by looking the pull request up rather than re-published;
- `dry_run=True` by default, so no remote object is created until the operator disables it;
  merging requires both `allow_merge=True` and `merge` in the request;
- commits only the files the gate approved (`request["files"]`), which `DispatchWorker` now
  collects from the validated worktree, capped at 512 KiB per file and skipped when binary.

Checks actually run:
| Check | Result |
| --- | --- |
| 12 GitHub tests (`test_factory_github.py`) | PASS: deterministic branch, dry-run makes no call, missing token and missing content refused, branch/commit/PR sequence, merge gated twice, token never echoed, reconcile found/absent/unknown |
| 109 factory tests | PASS |

At that point no real GitHub call had been made. The section below records the first real one.

## First real GitHub publication — develop → PR, no merge — 2026-11-01

Owner instruction in chat: target `https://github.com/OualidGuennif/aeion-autonomous-forum`,
base branch `develop`, classic `develop → PR → main` flow, token already in the host environment
file. The token value was never read by the assistant: a loader fills the process environment and
only non-secret metadata is printed. The permission check reported `admin, maintain, push, pull,
triage`; the repository is public and its only branch was `main`.

Actions, in order:
1. Read-only probe (`demo/factory/gh_probe.py`): repository reachable, `develop` **absent** (404),
   `main` present. No mutation.
2. `develop` created from `main@7193f5c9` (`demo/factory/publish_once.py --create-base`).
3. One factory build for feature 001 published through the real gate and `GitHubForge`
   (`--for-real`, dry-run disabled, merge never requested).

Result: pull request **#1**
`https://github.com/OualidGuennif/aeion-autonomous-forum/pull/1`, base `develop`, head
`aeion/build-1d3dfc59f2b2410c98db2195`, one added file `demo/forum/product/001-impl.md`,
`mergeable: true`, **not merged**.

Checks actually run:
| Check | Result |
| --- | --- |
| Read-only probe | PASS: repo 200, `develop` 404 before creation, `main` present |
| `develop` creation | PASS: `base_created:develop@7193f5c9` |
| Gate before publishing | PASS: `gate passed` (`scope`, `spec_unchanged`), artifact digest `bd7300ac…` |
| Publisher decision | PASS: `published`, `dry_run: false` |
| Pull request verified by API | PASS: state `open`, base `develop`, 1 file `added`, mergeable |
| Dry-run rehearsal before the real run | PASS: same gate, `dry_run: true`, no remote object |

A defect was found and fixed by this run: the publisher request did not carry `feature_id`, so the
first pull request was titled `Feature None`. `DispatchWorker` now sends `feature_id` and a
`title`, and PR #1's title and body were corrected through `demo/factory/gh_admin.py`.

Still not done: nothing was merged, `main` was not touched, and no CI workflow was waited on. The
committed file is the factory's **simulated** placeholder — this run proves the frozen build →
protected checks → publisher path against a real forge, not that feature 001 is implemented.

## Architecture integrations activated in an agent clone — 2026-11-01

Owner instruction: activate Graphify and Archify in the template when the factory clones the
product repository into an agent workspace.

`demo/factory/analysis.py` implements the preparation step: `clone()` shallow-clones a branch,
`activate()` runs the template's pinned `tools/architecture/setup` and verifies both integrations,
`prepare()` composes them and reports the Pi extension, `tools_available()` fails early when
`git`/`node`/`python3` are missing. Installation stays inside the ignored `.aeion/integrations`
and never edits a tracked file.

Real run against the target repository:

```
demo/.local/venv/bin/python demo/factory/analysis.py \
  --repo-url https://github.com/OualidGuennif/aeion-autonomous-forum \
  --dest demo/.local/factory/agents/aeion-autonomous-forum --branch develop
```

Result: `status: activated`, `graphify: true` (`0.9.97`, revision `0a8cd4e1…`),
`archify: true` (revision `208acba8…`), branch `develop`.

Harness prerequisite recorded for later, on the owner's instruction: Pi must be started with
`pi -e .pi/extensions/factory/index.js`, otherwise **the factory skills and hooks never load**.
`flue run` 2.3.0 has no `-e`/`--extension` option, so the flag belongs to the Pi invocation Flue
drives. The factory does not silently assume it: `pi_extension()` reports `present` and
`required_flag`, and the runbook states that `present: false` means unqualified.

Checks actually run:
| Check | Result |
| --- | --- |
| 14 analysis tests (`test_factory_analysis.py`) | PASS: pinned revisions, missing template/setup, activated/already-active, failed and partial install, shallow branch clone, non-empty destination refused, prepare composition, Pi extension present and missing |
| Real clone + activation | PASS: `activated`, graphify `0.9.97`, archify `208acba8…` |

## Duplicate-request guard against double billing — 2026-11-01

Owner report: harnesses sometimes submit the same turn twice, once as a prompt and once as a JSON
payload, and the same work is paid for twice.

The relay already forwarded **one** request per turn and performed no retries, redirects or proxy
use. The gap was that two byte-identical submissions were both forwarded. `demo/app/relay.py` now
hashes the accepted body and refuses a repeat of the immediately preceding body with
`409 DUPLICATE_REQUEST`, recording `context.duplicate_refused` before counting or forwarding — a
duplicate is never billed and never increments `forwarded_count`. A genuinely new turn has a
different body (the conversation grew) and is forwarded normally.

Checks actually run:
| Check | Result |
| --- | --- |
| 2 duplicate-request tests (`test_runtime.py`) | PASS: identical body → 409 and exactly one upstream request; a different body after a duplicate is still forwarded |
| Relay runtime tests | 7 tests PASS |

This guard covers the relay boundary this project owns. It does not prove the behaviour of the
upstream harness itself: if a future Flue/Pi version submits two *different* bodies carrying the
same instruction, the guard cannot see that, and the fix belongs in that harness.

## Tier-3 containment unblocked on macOS — copy-out transport wired into the runtime — 2026-11-01

The `EACCES` blocker is closed. The cause was measured, the transport was built, and it is now
wired into the agent runtime rather than only proven in isolation.

Cause: on Docker Desktop the labeled work volume is a **bind-backed** Docker volume. Inside the
OpenShell sandbox a write *lands* while the syscall returns `EACCES`; directory listings also fail
intermittently, and a file created by the sandbox is not writable by the host user (and the
reverse). Reads through the mount are equally unreliable.

Change, all in `demo/app/`:
- `sandbox.py` — `seed_in()` copies host files into the sandbox over the exec channel;
  `collect()`/`materialize()`/`sync_out()` bring results back. `materialize()` skips unchanged
  files, replaces read-only targets, and fails closed with `SANDBOX_SYNC_TARGET_LOCKED`.
- `runner.py` — for tier 3 only (`copies_out()`): the workspace is seeded into
  `/tmp/aeion-out/workspace`, `AEION_WORKSPACE` points there, and the agent's writes are collected
  back after it stops. The acceptance checker **never** reads the mount: the artifact is seeded
  into the fresh check sandbox for every isolated runtime, and permissions are normalised so the
  sandbox UID can read what the host wrote.
- `relay.py` — the upstream call now uses a real trust store (certifi) and no longer fails a live
  run with `TRANSPORT_ERROR`.
- `audit.py` — bounded failure metadata (`aeion.failure.type`) and `aeion.sandbox.files` added to
  the allowlist; free-form detail stays rejected.
- `settings.py` — the owner's single private file at the repository root is the primary source,
  the demo's stack file second; values are never logged.

Checks actually run:
| Check | Result |
| --- | --- |
| `tests/qualify_flue.py` (real OpenShell, fake inference, all three tiers) | **PASS** — tier 3: 12/12 checks, 2 agents, 6 requests; tier 2: 12/12, 5 requests; tier 1: 8/8, 5 requests |
| Qualification marker | written and bound to the current protocol hash, so `cli_qualified()` is true |
| **Live tier-3 run** (real OpenCode model, real OpenShell sandbox, `pricing-js-v1`) | **PASS** — `status: passed`, `check 12/12`, `changed: true`, `usage_complete: true`; events show `sandbox.seeded` → agent → `sandbox.collected` → `sandbox.retired` → `artifact.checked` |

This is the first time a live model has run to completion inside a real OpenShell sandbox on this
machine. What it still does not prove: production multi-tenant isolation, a Linux VPS run, or that
the sandbox survives a hostile model (that is the trust model's subject, not a test result).

## Independent deterministic reviewer gate — 2026-11-01

Owner question: what happens if the model behind an agent turns rogue and wants to destroy
everything? A second LLM reviewer would be untrusted input too, so the reviewer is **rules**.

`demo/factory/review.py` reviews the bounded diff the artifact gate already accepted and returns
`approved`, `held` or `refused`, with a content-addressed digest (same bytes → same verdict;
different bytes → different digest, so an approval cannot be replayed onto another diff). It
refuses paths outside the accepted diff and empty diffs; it holds credential-shaped strings,
destructive or remote-execution patterns, dependency manifests, binary content, oversized files
and oversized diffs. `DispatchWorker` runs it between the protected checks and the publisher, and
`Publisher.decide` independently refuses to publish without `review_status == "approved"`.

Checks actually run:
| Check | Result |
| --- | --- |
| 13 reviewer tests (`test_factory_review.py`) | PASS: approval, determinism, digest over content, refusal precedence, secrets, destructive commands, manifests, binary, size and count bounds |
| 2 wiring tests (`test_factory_s3.py`) | PASS: a secret holds `owner_review_required` with no receipt; an empty diff fails the build |
| Factory suite | 136 tests PASS |
| Full `demo/tests` suite | 187 tests, 1 pre-existing `ps` denial |

The trust model, including what a rogue model can still do, is written in
`demo/factory/trust-model.md` and linked from the runbook.

## `main` protected on the product repository — 2026-11-01

Owner instruction: protect `main` on `OualidGuennif/aeion-autonomous-forum`, with `gh` access.
Applied through the GitHub API using the authenticated `gh` session (account `OualidGuennif`,
`repo` scope). Before the change the branch answered `"Branch not protected"` (404) and the
repository had no ruleset.

Effective state, read back from the API:

| Setting | Value |
| --- | --- |
| Pull request required | yes, with 0 required approvals so a solo owner can still merge |
| Dismiss stale reviews on new pushes | yes |
| Enforce for administrators | **yes** — the owner cannot push or force-push directly either |
| Force pushes | blocked |
| Branch deletion | blocked |
| Conversation resolution | required |
| Delete head branch on merge | enabled repository-wide, so factory branches do not accumulate |

`develop` is deliberately **not** protected yet: the factory opens pull requests into it and
protecting it was not requested. The same call adds it.

What this proves: the setting is applied and enforced by GitHub. What it did not prove at the
time: that the repository's CI, review or release process is adequate — there were no required
status checks. The section below closes that gap.

## `develop` protected, required checks on both branches, product contract in CI — 2026-11-01

Owner instruction: "Protéger develop aussi", add a mandatory CI check, and take the CI from
`aeion-factory`. The product repository already carried the template's `.github/workflows/ci.yml`
verbatim, so the work was to give it something real to say and then make it binding.

**A fifth check, independent of the factory.** `.github/scripts/check_product.py` re-enforces the
artifact contract on the pull request: regular files only, 64 KiB per file and 1 MiB in total,
UTF-8 text with no NUL byte, no credential-shaped string, and a Markdown artifact that starts with
a heading naming its feature id. The build worker already runs its own review; a gate that only the
gated party can run is not a gate, so this is the second opinion. It is a no-op until the first
artifact lands, which is why it could become required immediately. Added in
[PR #2](https://github.com/OualidGuennif/aeion-autonomous-forum/pull/2) — CI green, squashed into
`develop` (`e79080ab`).

**Protection applied to both branches** through the API, then read back:

| Setting | `main` | `develop` |
| --- | --- | --- |
| Pull request required | yes | yes |
| Required checks | `Knowledge, links and repository health`, `Product artifacts`, `secret-scan`, `dependency-scan`, `sast-scan` | same five |
| Branch up to date before merge | yes | no (parallel builds) |
| Enforce for administrators | yes | yes |
| Force push / deletion | blocked / blocked | blocked / blocked |
| Linear history, conversation resolution | yes | yes |

**Refusal proven, not inferred.** A probe commit pushed straight to each branch was rejected by
the server:

```
! [remote rejected] probe-direct -> develop (protected branch hook declined)
remote: - Changes must be made through a pull request.
remote: - 5 of 5 required status checks are expected.
! [remote rejected] probe-direct -> main (protected branch hook declined)
```

[PR #1](https://github.com/OualidGuennif/aeion-autonomous-forum/pull/1) was closed with its
branch deleted: it carried the S3 simulated artifact, which does not satisfy the new contract and
was never meant to merge.

## One GitHub key per capability — 2026-11-01

Owner question: "comme on ne peut pas faire confiance à l'AI il nous faut plusieurs clés GitHub
avec restriction ou autorisation, c'est bien ça ?" Yes — and the factory now encodes it.

`demo/factory/keys.py` owns the table: `GH_BUILD_KEY` (build, `contents:read`), `GH_API_KEY`
(publish, `contents:write` + `pull_requests:write`), `GH_RELEASE_KEY` (release, human only),
`OPENCODE_API_KEY` (inference). `assert_only()` refuses a role a process does not need,
`assert_worker_isolated()` refuses publish or release keys beside a worker, the publisher exits 2
when it sees an inference or release key, and `demo/app/settings.py` scrubs the whole publish class
at start-up. The committed root `.env.example` states the same contract for the owner, and
`test_factory_keys.py` fails when the template and the code drift apart.

Same date, the publisher stopped trusting a receipt without a circuit: `verified_receipt()` now
requires `circuit.status == "approved"` **and** at least two votes, so the previously valid
"no circuit at all" receipt is refused (`test_factory_pipeline.py`, 8 tests).

## Release plane built and drilled — 2026-11-01

Owner request: deterministic releases, staging visible in the front, **Validate** promoting to
production, step-by-step rollout (25% / 6 h, 50% / 12 h, 100%) behind a real load balancer and Redis
cache, deterministic monitoring, an "immediate full deploy" button and real feature flags. Product
stack: Quarkus + Java 25.0.4 + Hibernate + SQLite as a separate service + Kafka + React Native.

Built: `demo/factory/release.py` (content-addressed record, monotone bucketing, plan as data),
`demo/factory/canary.py` (pinned policy, four verdicts), `demo/factory/releases.py` (staging,
promotion, samples, flags, persistence), `demo/deploy/cache.py` (Redis RESP client plus file
fallback), `demo/deploy/playground.py` (reverse proxy, two slots, staging slot, sticky cohorts,
cache, counters), cockpit endpoints and the front panel, and `demo/factory/gateway.py` for
short-lived agent sessions.

Run with a real Redis (`docker run … redis:7-alpine`, `AEION_REDIS_URL=redis://127.0.0.1:6399`),
`demo/factory/drill_release.py`, compressed by 1/3600 and recorded on the release:

| Step | Result |
| --- | --- |
| build 001, 002, 003 | gate passed, circuit approved with two distinct families, `simulated_complete` |
| stage | `staged`, 0% of production, staging slot serving the bundle |
| validate | 25%, `stable_bootstrapped` (first release also fills the empty prod slot) |
| 4 monitor samples + gate | `continue` |
| advance | 50%, then 100%, state `released` |
| traffic | 580 requests, 580 `2xx`, 0 `5xx`, cache `backend: redis`, 580 hits, p95 1.83 ms |

Honest limits: inference is **simulated** (`deterministic_answer`, receipts say `simulated: true`),
so this proves the mechanics — gate, circuit selection, queue, release, routing, caching, sampling —
not that a model judged the code. The 6 h/12 h dwells were compressed and the factor is stored on
the release. The Quarkus/Java/SQLite/Kafka/React Native stack is recorded as the target in
[RELEASES.md](RELEASES.md) §8. At the time of this drill no Java code existed; the service was
built afterwards and its evidence is the section below.

**Two authentication planes.** Workers get short-lived `aeion_…` sessions from the gateway
(15 min, `github:read` only, repo-pinned, audited, revocable); forum users authenticate with
username/password in the Quarkus service. A worker session is not a forum credential.

## Product service on Quarkus 3.40.1 and Java 25.0.4 — 2026-11-01

The forum stopped being a plan. `demo/forum-app/` is a Gradle project that builds and runs on the
machine, and features 001, 002, 003 are implemented in it with their acceptance checks as tests.

| Claim | Command that proved it |
| --- | --- |
| Java 25.0.4 | `java -version` → `java 25.0.4 2026-01-20 LTS` |
| Gradle 9.8.2, not Maven | `demo/.local/tools/gradle-9.8.2/bin/gradle --version` |
| Quarkus 3.40.1 boots | `java -jar build/quarkus-app/quarkus-run.jar` → `powered by Quarkus 3.40.1 ... started in 1.348s` |
| 36 tests green | `gradle test` → `TOTAL 36 tests, 0 failures, 0 errors` |
| SQLite really used | `/api/schema` → `applied [V1]`, `expected 1`, `pending 0` |
| Settings round-trip | `PUT /api/settings/forum.name` 200, `GET` 200 with the same `updated_ns` shape, unknown name 404 |
| Accounts | `POST /api/auth/register` 201, first account `role: owner`, duplicate 400 `username_taken`, short password 400 `weak_password` |
| Sessions | `POST /api/auth/login` 200 + `Set-Cookie` HttpOnly, `SameSite=Strict`; `GET /api/auth/me` 200; `POST /api/auth/logout` 200 then `me` 401 |
| Lockout | five wrong passwords → five 401 `invalid_credentials`, then 423 `account_locked` even with the right one |
| Hashes | `sqlite3 ... "select substr(password,1,10) ..."` → `$argon2id$`; session `id` is 64 hex characters, never the cookie |
| Signed cookie | an edited cookie → 401 `unauthorized` before any database lookup |
| Body cap | a 20 KB register body → 413 |
| Fail closed | without `AGORA_SESSION_SECRET`: `IllegalStateException: session_secret_missing: AGORA_SESSION_SECRET is required and was not provided`, no listener; `changeme` → `session_secret_placeholder`, no listener |

Built: `ForumHealth` (`/healthz`, `/__release`), `Setting` + `SettingsResource`, `Migrations` +
`MigrationRunner` (`/api/schema`), `ForumClock`, `SessionSecret`, `StartupChecks`, `AuthService` +
`AuthResource`, `db/migration/V1__initial.sql` (settings, accounts, sessions, threads,
schema_events) and `index.txt`.

**Feature 003 is the test harness, and it earned its place immediately.** `EphemeralDatabase`
creates a marked, isolated SQLite file under `build/test-db/`, applies the application's own
migration resources through `Migrations`, freezes the clock, and deletes everything on close. Its
three acceptance checks from the brief are tests: two databases run at once without interfering, a
row left by one is absent from the next, and a path that is not disposable is refused **before any
DDL** (four refusals: outside `build/`, a production-looking name, an existing unmarked file, and a
missing marker).

It found a real defect on its first run. `Migrations.statements` dropped any chunk that began with
`--`, so `V1__initial.sql` lost its `CREATE TABLE settings` while the ledger recorded `V1` as
applied: the service booted "successfully" and answered `500 no such table: settings` on the first
request. Fixed by stripping whole-line comments before splitting; `MigrationsTest` now asserts every
table the migration declares exists, that a second run applies nothing, and that a failing migration
rolls back and records no version.

Honest limits: accounts, sessions and signing are features 004/005 and went in ahead of their turn in
the plan, so the factory's staged release `c60a7f42...` still describes 001-003 only. The Kafka
producer/consumer is configured but no broker was contacted. `demo/forum-db/` (the separate SQLite
service with snapshots and a restore drill) is not built. The React Native front does not exist yet.

## SQLite guardian service, drilled on the live database — 2026-11-01

Owner requirement: SQLite "deployed separately with true protection and resilience". `demo/forum-db/`
is that service: it owns survivability, not SQL. The forum keeps its JDBC connection; the guardian
gives the file what an embedded file never has — a second integrity opinion, snapshot history with
digests, a restore drill, and a lease that makes two writers impossible.

| Claim | Evidence |
| --- | --- |
| 18 service tests green | `unittest discover -s demo/tests -p "test_forum_db_service.py"` → `Ran 18 tests ... OK` |
| WAL and a busy timeout are not optional | `PRAGMA journal_mode` → `wal`, `PRAGMA busy_timeout` → `5000` |
| A missing database is refused, not created | `test_a_missing_database_is_refused_not_created` asserts the file is absent after the refusal |
| Snapshots stay consistent under a live writer | 5 snapshots taken while 200 settings were written through the forum's HTTP API: all `integrity: ok`, 73 728 bytes |
| A drill, not a promise | restore drill on the live file: `ok`, `unchanged_source: true`, lag 0 on every table |
| Retention is bounded and reported | keep 3 → `pruned` two names, three retained |
| One writer | a second `take_writer_lease()` on the same file → `writer_lease_held` |
| A snapshot that lost a table is refused | `test_restore_drill_refuses_a_copy_that_lost_a_table` (drop `threads`) |
| An older snapshot is accepted with its lag | `test_restore_drill_accepts_an_older_snapshot_and_reports_the_lag`, lag reported per table |
| The live file is never written by a drill | source digest compared before and after; a drill copies first |

Run against the real service: `PYTHONPATH=demo demo/.local/venv/bin/python demo/forum-db/drill.py
--database /tmp/agora.db --snapshots /tmp/agora-snapshots --keep 3 --writes 200` → exit 0,
`ok: true`.

Design decisions worth recording:

- **Row counts never fail a drill.** An hour-old backup legitimately has fewer rows; a check that
  refused it would refuse every real restore. A missing *table* is a different fault and is refused.
- **It does not proxy SQL.** An HTTP hop inside a transaction would trade correctness for a diagram.
  The service is a guardian; the application stays the single writer by contract, enforced by lease.
- **Missing and corrupt are different answers.** `healthz` says 503 `unavailable` for an absent file
  and 503 `corrupt` for a failed `quick_check`.

Honest limits: snapshots share a disk with the database (no off-host copy), there is no PITR, and the
service neither starts nor supervises the application. Those are named gaps in
[forum-db/README.md](../forum-db/README.md).

## Threads, the outbox, and a real Kafka broker — 2026-11-01

Feature 010 is a thread; feature 011 is the event leaving the request path. Both are wired to a real
broker, not a stub, and the failure path was exercised with the broker actually stopped.

| Claim | Evidence |
| --- | --- |
| A thread and its event are one transaction | `threads.create` persisting the row and the `thread_outbox` insert in the same `@Transactional`; `ThreadServiceTest` asserts the event exists with `pendingCount() == 1` |
| The broker is not trusted to create topics | `KafkaTopics.ensure` lists, then creates `agora.threads` with 3 partitions; auto-creation stays off |
| Produce works against a real broker | `POST /api/threads` 201 → `thread_outbox.published_ns` set, `attempts 0` |
| The event is consumed | `thread_event_log` holds it with topic `agora.threads` and a 244-byte payload |
| A replay is applied once | republishing the same `event_id` (published flag reset) → `pending 0`, `thread_event_log` still 1 row, log line `already applied: replay ignored` |
| A broker outage does not fail the request | broker stopped, `POST /api/threads` still 201; the row waits with `attempts 1` and `last_error: kafka_send_failed: TimeoutException: Topic agora.threads not ...` |
| Recovery drains the outbox | broker started → both rows published, `thread_event_log` 2 |
| A misconfiguration is refused, not guessed | the first attempt failed with `ConfigException: delivery.timeout.ms should be equal to or larger than linger.ms + request.timeout.ms`; the producer now sets `request.timeout.ms=3000`, `delivery.timeout.ms=10000`, `acks=all`, `enable.idempotence=true` |
| 46 tests green | `gradle test` → `TOTAL 46 tests, 0 failures, 0 errors` |

Broker used: `docker run -d --name aeion-kafka -p 127.0.0.1:9092:9092 apache/kafka-native:4.2.0`
(single node, KRaft). The application is started with `AEION_KAFKA_ENABLED=true
AEION_KAFKA=127.0.0.1:9092`; with the flag off, the same jar serves readers and leaves events in the
outbox, which is the default.

Honest limits: the consumer group is a single instance, so partition rebalancing is untested; there
is no dead-letter topic (a record that always fails is retried and logged rather than parked); topic
creation assumes the application may create topics, which a locked-down cluster would refuse.

## React Native front, bundled and smoke-tested — 2026-11-01

`demo/forum-mobile/` is the forum's front on **React Native 0.88.1** through **Expo SDK 58**, in
TypeScript: thread list, session screen, compose screen, and one API client that owns the cookie.

| Claim | Command | Result |
| --- | --- | --- |
| Types are sound | `npx tsc --noEmit` | exit 0 |
| It bundles for a device | `EXPO_NO_TELEMETRY=1 npx expo export --platform ios` | `iOS Bundled 5282ms index.ts (619 modules)`, 1.6 MB Hermes bytecode |
| The client works against the live forum | `npm run smoke` | 11 steps: health, guest listing, register, login (87-char signed cookie), create, read back, list contains it, 401 without a session, 401 on a wrong password, logout, 401 after revocation |
| The two auth planes stay separate | the client sends only `Cookie: agora_session=...`; a worker-style cookie is refused | `ThreadsResourceTest.readingIsPublicCreatingIsNot` |

Honest limits, stated in [forum-mobile/README.md](../forum-mobile/README.md):

- **No simulator or device run.** The bundle compiles and the network contract is proven end to end;
  no screenshot, gesture or layout was checked on a screen. The UI is unverified.
- **No UI test suite.** The screens are covered by the typechecker and the bundler only.
- **The session lives in memory**, so closing the app signs the user out.
- **Thread detail does not navigate yet**: the endpoint is proven by the smoke test, not by a screen.

The smoke test exists because a screenshot would not have proven the thing most likely to be wrong:
React Native does not expose `Set-Cookie` consistently, so the client parses the login response and
replays the cookie itself. That is exactly the part a simulator can hide and a script cannot.

## The same front in a browser — 2026-11-02

The owner asked for the forum to be reachable "depuis l'app soit depuis juste un site internet en
react natif". The client is therefore rendered by `react-native-web` as well: one source, two hosts.

| Claim | Command | Result |
| --- | --- | --- |
| It renders in a browser | `npx expo start --port 8082`, headless Chrome on `http://127.0.0.1:8082` | thread list drawn from the live API, footer `release unreleased · runtime 25.0.4` |
| The browser may read the forum | the page's own `/api/threads` call | threads rendered without a session |
| The browser may open a session | `curl` with `Origin: http://127.0.0.1:8082` | preflight 200, `access-control-allow-credentials: true`, login 200 with `Set-Cookie` |
| The browser may write | same origin, cookie jar plus `X-CSRF-Token` | create 201; **403 without the token** |
| Nothing regressed on the device path | `npm run typecheck` / `npm run smoke` / `expo export --platform ios` | exit 0 / 12 steps / 1.5 MB Hermes bundle |

Two changes made it work and are worth knowing:

- **The cookie changes owner.** A browser hides `Set-Cookie` from JavaScript and forbids a `Cookie`
  header, so `src/api.ts` sends `credentials: 'include'` and lets the jar hold the session; on a
  device it keeps parsing and replaying the header as before. The CSRF token comes from the login
  body either way, so mutations still carry `X-CSRF-Token`.
- **The API allows exactly two origins**, `http://127.0.0.1:8082` and `http://localhost:8082`, with
  credentials and nothing else (`quarkus.http.cors.*`). The session cookie stays `SameSite=Strict`,
  so the page and the API must share a host name — open `127.0.0.1:8082`, not `localhost:8082`,
  against an API on `127.0.0.1:8081`.

Honest limit: no human has looked at it. The browser build was rendered headlessly and screenshotted;
Expo Go was installed on a booted simulator but this Xcode ships no `Simulator.app`, so the native
screen was never inspected.

## Two real Quarkus instances behind the release plane — 2026-11-01

The release plane decided routing against synthetic bundles. It now decides it against **two running
forum instances**: the built jar, two SQLite files, two `AEION_RELEASE` values, registered as the
`stable` and `canary` backends of `deploy/playground.py`.

| Claim | Evidence |
| --- | --- |
| A slot can serve a real application | `playground.backend("stable", "127.0.0.1:<port>", release="stable-real")`; `has_release` is true without a bundle |
| The percentage decides which instance answers | 200 requests through the balancer at 25% → `{"canary": 40, "stable": 160}`, `expected_canary: 40`, `canary_matches_routing: true`, all `200` |
| The cache answers the second request | `X-Cache: miss` then `hit`, same body, backend `redis` |
| A dead upstream is a 502, not a hang | `test_a_dead_upstream_is_a_502_not_a_hang` |
| An invalid upstream is refused | `test_an_invalid_upstream_is_refused` (https, unknown slot) |
| The counters are honest | `requests 202`, `status_2xx 202`, `status_5xx 0`, `cache_hits 199`, `p95 0.34 ms` |
| 341 demo tests | `unittest discover -s demo/tests` → 341 tests, 1 known macOS `ps` error in `test_openshell_setup` |

Run: `PYTHONPATH=demo AEION_REDIS_URL=redis://127.0.0.1:6399 demo/.local/venv/bin/python
demo/deploy/drill_real_slots.py --requests 200 --percent 25` → exit 0, `ok: true`.

Honest scope: the drill drives **GET** traffic (`/healthz`, `/api/threads`) because the balancer and
its cache are GET paths today. Promotion, canary verdicts and the 6 h/12 h dwells still live in
`factory/releases.py` and are unchanged by this: what was missing was the data plane talking to the
real service, and it now does.

## CSRF tokens on every mutation (feature 006) — 2026-11-01

The forum accepts cookie-authenticated writes, so a cross-site form could have posted as a logged-in
user. `CsrfGuard` now refuses any mutation that carries a session cookie without that session's token.

| Claim | Evidence |
| --- | --- |
| The token is session-bound and unforgeable | `SessionSecret.csrfFor(token)` = HMAC-SHA256, same key as the cookie signature; `csrfMatches` compares with `MessageDigest.isEqual` |
| It is accepted in a header only | `X-CSRF-Token`; no query parameter, no form field |
| A cookie without its token is refused | live: `POST /api/threads` with the cookie, no header → `403 {"error":"csrf_invalid"}`; with the token → `201` |
| A wrong token is refused | `ThreadsResourceTest` sends `not-the-token` → 403; `AuthResourceTest` asserts logout without the token → 403, with it → 200 |
| Reading is untouched | `GET /api/threads` with the cookie still returns 200 |
| The app client sends it | `demo/forum-mobile` `npm run smoke` → 12 steps, including `login — cookie 87 chars, csrf 43 chars` and `refuses a mutation without its CSRF token — 403` |
| 47 Java tests | `gradle test` → `TOTAL 47 tests, 0 failures, 0 errors` |

Why a derived token rather than a stored one: it needs no table, it cannot drift from the session, it
dies when the session dies, and a leak of the database grants neither half. The exemption is explicit
and narrow: **no cookie means no CSRF check**, which is exactly `register` and `login` — the credential
exchange itself — and an unusable cookie is answered 401 by the resource, which says more than a 403.

## Plan C: one pinned feature, the real check and a Langfuse trace — 2026-11-02

The first feature built through a pinned target is **013 Security headers**, adapted to the
runnable Quarkus JSON API. `demo/forum/targets/forum-app-013.json` pins base
`753ba3ed239560f2854921efb10530916dcc57ab`, the `demo/forum-app/src/` main and test scopes, the
adapted brief and the protected contract test. The 100-feature manifest is unchanged.

| Claim | Evidence |
| --- | --- |
| One real build, no paid model | injected fake builder writes `SecurityHeadersFilter.java` and its test; `cost_reservation_usd = 0.00` |
| The real suite judges it | `gradle -p <clone>/demo/forum-app test --offline --no-daemon` → return 0, 27,596 ms; contract SHA-256 `23706825…a07d` |
| The contract is outside the candidate | `demo/forum/targets/forum-app-013/SecurityHeadersContractTest.java`, copied into the clone and removed after the run; not tracked at the base |
| The receipt has the identity | build `26b29b2f9fb34083b0a737fc92ec4766`, attempt `5518a5d638d34a848fcaf1df9915fa92`, artifact `6b78a27a…41b1`, feature `013`, base `753ba3e` |
| Langfuse has the trace | trace `0ea7e7625fc2109a535817c6f7eeabdd`; `factory.build` read back with build/feature/attempt/artifact/session matching |
| The cockpit sees it | the build is in `demo/.local/factory/factory.db`; the receipt line links `/trace/<id>` |
| Safe refusals | missing base → `base_unavailable`; builder error or failed check → `FAILED`, no publisher |

Run: `demo/.local/venv/bin/python demo/tests/qualify_forum_build.py`. The fake forge records a
PR shape but never contacts GitHub; no branch, pull request, deployment or paid inference exists.
The model is fake, so this validates the adapter, check and telemetry path, not model quality.
