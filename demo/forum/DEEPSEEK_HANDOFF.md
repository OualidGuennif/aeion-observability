# DeepSeek handoff — build the factory, not the forum

Prepared: **2026-11-01, Europe/Paris**. Status: **awaiting_owner_github_confirmation**.

**START GATE — WAIT FOR THE OWNER.** Do not start implementation, S1–S4, test/worker runs,
agent dispatch or provisioning when you wake. First wait for the owner's explicit confirmation
that the repository-restricted GitHub credential has been placed in the intended host `.env`.
You may read this handoff and report that you are waiting. Elapsed time, a wake-up, previous
broad approval, or detecting a credential is not that confirmation. Record the owner's message
reference/time, never the credential, when the gate is lifted. This instruction supersedes any
earlier instruction to start automatically.

This file is the pickup point when the existing DeepSeek session wakes. It does not create or
reschedule a wake-up, authorize model spending, or assert that a background job exists.

## 1. Owner intent and authorized scope

The owner wants a secure local frontend where they can inspect 100 Markdown feature cards,
launch one, queue up to ten, and observe the underlying work. Flue builders eventually implement
Agora from those files. You implement the surrounding factory: board, queue, dispatch, gates,
publisher policy, observer and operational runbook. **Do not hand-build the forum.**

The current owner message explicitly requests plan/spec corrections **under `demo/` only** and
this execution handoff for the local factory continuation. Follow the existing plan/build/test
skills, but start the local slices only after the START GATE above is lifted. That explicit
confirmation releases the existing local continuation scope; do not ask again for every slice.
It does not enlarge that scope to spending, remote operations or deployment.

Keep all writes under `demo/`, including evidence/task state. Do not modify root `work/`,
`CHANGELOG.md`, `.github/`, `knowledge/`, harness configuration outside demo, sibling projects or
Git configuration. Preserve existing changes. Do not reset, stash, delete, stage or commit them
blindly. Remote pushes, PRs/merges, credentials, paid/live calls and deployment remain disabled
until explicitly enabled through the owner's authorized workflow.

## 2. Read before editing

1. Repository `AGENTS.md` and applicable skills, then current `git status --short` and diff summary.
2. [PLAN.md](PLAN.md): product contract, phase partition and invariants AG-01…AG-09.
3. [ECOSYSTEM.md](ECOSYSTEM.md): factory interfaces and invariants FX-01…FX-10.
4. [Validation](VALIDATION.md), [feature index](features/README.md) and generated manifest.
5. Only relevant portions of `demo/README.md`, `demo/app/server.py`, `runner.py`, `profiles.py`,
   `demo/flue/src/` and their existing tests. Never read credential files or raw transcripts.

This handoff supersedes the pasted chat's stale claims that S1 was being built or that there
was no blocker. A historical parked draft was mentioned in chat but was not verified in this
pass: do not assume its existence, test results or safety, and do not execute it blindly.
The current branch was `adopt/factory-1.8.2`; preserve it. Product paths are planned, not populated.

## 3. What changed and why

- Product output is exclusively `demo/forum/product/`. Existing `demo/app/` and `demo/flue/`
  contain trusted host execution and cannot be builder-writable or auto-merge eligible.
- Every catalog entry now declares phase, builder tier 3 and literal write scopes. IDs need not
  be topologically sorted. A real cycle and a later-phase prerequisite are rejected separately.
- 077, 082 and 086 have disjoint outputs and may run concurrently after their prerequisites.
  Everything else is exclusive. Initial factory active concurrency remains one.
- Foundational rules/permissions and scoped identities move earlier. Storage starts held and
  has no live writer; 063 later integrates mandatory guards without a storage/pipeline cycle.
- Source storage is normalized Markdown plus sanitized HTML, not original transport bytes.
  Injection filtering produces a separate agent excerpt; content never grants capabilities.
- Only agents publish discussion; human accounts are readers/operators. Three corpus categories
  remain three; citation truncation, quotas, snapshots and exports have explicit contracts.
- Gates are protected against candidate replacement. Review, gate and publisher must agree on
  repository/base/head/tree/spec/check-bundle identity, and cancellation revokes late effects.
- No direct forge token reaches builder or observer. Protected sensitive changes still wait for
  the owner. The observer proposes, and deterministic publisher code decides permitted effects.
- Authentication, CSRF, concurrent claims, crash recovery, cost reservation, telemetry canaries
  across OTLP surfaces and disposable restore proofs are explicit acceptance requirements.

## 4. Source of truth and safe regeneration

Canonical content lives in `demo/forum/tools/specs_a.py` through `specs_f.py`. The generated
100 Markdown files, index and MANIFEST.json must not be edited independently. Keep IDs stable.
The manifest schema version is 2; any future reader must reject unsupported versions.

```sh
python3 -B demo/forum/tools/generate_features.py
python3 -B demo/forum/tools/generate_features.py --check
python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
```

The same generator refreshes both review snapshots after plan changes, rebasing local links
for the extra `openAI/` directory level. Its `--check` also detects stale snapshots.

The generator checks metadata consistency; it is not the runtime permission enforcer or a
security certification. Runtime code must independently validate schema, paths and transitions.

## 5. Local implementation slices

Implement small coherent slices, inspect each diff, run relevant tests and record actual
results in `demo/forum/VALIDATION.md`. Do not mark a gate green from a model's narration.

### S1 — a usable board with honest fake execution

- Reuse the native cockpit, typography and ivory/forest-green/copper styling. Put the protected
  factory implementation under `demo/factory/`; use small routing integration in `demo/app/`.
- Parse schema-version-2 manifest and render all 100 cards with specs, phase, dependencies,
  parallel indicator, size and tier. Build one; explicitly queue up to ten selected IDs.
- Implement protected administrator sessions, API/SSE authorization, CSRF and Host/Origin/body
  checks before enabling mutations. Reader sessions cannot control the factory.
- Use SQLite transactions for queue/state/events, stable idempotency keys and bounded claims.
  Start with one active worker; prove exclusivity before enabling two disjoint parallel jobs.
- Use a fake worker, disposable repository and visibly simulated receipts. Missing dependencies
  are shown, not silently completed. Test scheduling with a separate labelled fixture catalog.
- Implement cancellation generation and late-result rejection, bounded SSE/reconnect and reload.

Proof: ten-item cap including running work; duplicate request replay; missing prerequisites;
exclusive/disjoint jobs; startup with malformed catalog; wrong/missing/expired sessions; CSRF
and cross-origin refusals; cancel-before/after work; restart without duplicate claims. Real
catalog features remain proposed unless actually built and qualified later.

### S2 — frozen dispatch and real containment, still fake inference

- Freeze the manifest/brief/base/check identities and configured bounds before worker launch.
- Adapt the existing tier-3 mechanism to an isolated product worktree, without writable factory
  or Git metadata. Validate a returned artifact against the actual Git diff before host commit.
- Use fake inference and a disposable local repository. A PR-shaped local receipt is labelled
  as such; it is not evidence of a GitHub operation.
- Supply the trusted narrow participant/moderator broker interface as factory infrastructure;
  product feature 066 later qualifies it. Never import product modules on the host or let its
  builder edit `demo/flue/` when an integration is missing.
- Qualify the approved macOS stdin-copy transport and Linux path before claiming live tier-3
  readiness. Restrict transfer/execute paths, sizes and permissions; preserve no egress.

Proof: real OS refusal of host/sibling/parent/symlink paths, shell/egress capabilities outside
policy and fake secrets; fresh-sandbox checks; round-trip artifacts and rejected mixed diffs.
If real containment cannot be qualified, keep live mode blocked and continue unaffected local
policy/UI work. Never relabel a mocked adapter as a successful security qualification.

### S3 — protected checks, publisher policy and observer proposals

- Keep the evaluator and qualification registry outside candidate control. Build its acceptance
  cases from the frozen specs; a missing check produces qualification_missing, not green.
- Match authorized review to exact artifact identity. Revalidate changed heads/bases and reject
  cancelled generations. Do not accept arbitrary PR comments as approval.
- Implement publisher decisions against fake forge responses first. Allow only the pinned target,
  actual reviewed diff and declared product write scopes; sensitive or mixed diffs hold.
- Reconcile an uncertain forge result before retrying. The observer sees only bounded metadata
  and emits deduplicated proposals; it cannot call merge or hold a forge credential.

Proof: candidate-replaced tests, forged receipt/issuer, stale SHA/base, forbidden target/path,
sensitive edit in an innocently named file, late completion after kill, and crash immediately
after external success but before local recording. Expected refusals must be asserted.

### S4 — local operational artifacts and disposable restoration

- Prepare VPS configuration/runbook locally, with only the intended public forum exposed through
  authenticated/TLS boundaries; factory/backends remain private. Actual deployment is separate.
- Specify and run a disposable SQLite restore. When the forum Postgres schema exists, also run
  its restore test with counts, content checksums, audit verification and readiness checks.
- Before the forum exists, a restored generic Postgres fixture is mechanism evidence only; mark
  actual forum restoration pending. Do not claim S4 fully qualified from an HTTPS probe alone.

## 6. Hard boundaries and current blockers

- The owner has not yet confirmed GitHub credential setup. Remain in
  `awaiting_owner_github_confirmation`; do not start even the local fake-inference slices.
- The requested external credentials are a repository-restricted GitHub credential for the host
  publisher and `OPENCODE_API_KEY` for the existing inference relay. The owner thinks the latter
  is already configured, but this has not been verified. Do not ask them to paste either key.
  Do not read, display or copy `.env`, dump an environment, or pass either key to an agent.
  After confirmation, use only the trusted host loader's minimal presence/readiness results;
  report a missing credential by its variable name only. The new GitHub publisher/loader is not
  implemented yet, so do not assume adding a variable alone makes the integration operational.
- DeepSeek profile expiration is 2026-10-31. Do not change its date merely to allow a run.
  Fresh upstream/privacy/counting qualification and explicit spending approval are still needed.
- Tier 2 restricts model-facing file tools, not host privileges. Unattended builders and forum
  profiles require actual confinement; allowlisted tool names are not sufficient evidence.
- The current main-target CI does not qualify feature PRs targeting develop. Preparing branch
  existence/protection/CI needs authorized scope outside this demo-only change. Remote mode holds.
- A fine-grained PAT can read other public repositories; their 200 status does not prove excess
  permission. Validate selected repo/write grants without destructive cross-repository probes.
- Root work/current.md and CHANGELOG.md were intentionally untouched due the owner's scope.
  Record local state here; root sign-off housekeeping is deferred, not falsely declared done.

## 7. Definition of local delivery

The owner can open the local factory, inspect/select the 100 specs, queue fake builds, follow
state/check/usage rows and stop work effectively. Tests prove the refusal/recovery behavior.
Actual qualified product builds, paid calls, remote operations and deployment are separately
identified; the UI never presents simulations or unknown outcomes as successful real delivery.

At each stopping point record files changed, exact commands/results, remaining gates and the
next concrete action. If context resets, persist a fresh bounded handoff under `demo/` before
continuing. This document grants no permission beyond the owner's actual instructions.
