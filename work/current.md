# Current work

Updated 2026-11-12. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Contract Scope Bounding & Correction Deadlock Resolution — IN PROGRESS

- Owner decision: resolve author/reviewer deadlock on Feature 003 where hallucinated acceptance contracts forced out-of-scope edits (64K transport cap, row-hiding filter, HTTP clock freeze) rejected by reviewers, eliminate blind contract reuse in `factory-correction:`, and mark `reprepare_needed` on `correction_unchanged`.
- State: `product_checks.py:acceptance_prompt` bounds tests strictly to frozen specification deliverables, forbids unrequested endpoint assertions, and documents the 16KiB HTTP transport cap; `preparation.py` auto-detects reviewer rejection or contract-scope conflicts in previous builds and sets `reprepare_needed = True` rather than blindly copying flawed `acceptance.mjs`; `dispatch.py` marks `reprepare_needed` on `correction_unchanged` ($\le 1500$ lines); tests pass.
- Next: run admission requalification, restart cockpit daemon, cancel stuck build, relaunch clean Feature 003.
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

## Sandbox Provisioning Resilience & Quarkus Lifecycle Hardening — COMPLETED

- Owner decision: prevent recurrence of sandbox EPERM / container naming races, preserve reasoning effort 'max', specify Quarkus injection SPI, and ensure role teardown safety.
- State: `setup.py:normalize_tls_permissions` fixes supervisor EPERM; `sandbox.py` introduces non-colliding attempt hashes (`ae-<root>-<run>-<agents><role>`), bounded retries with backoff, and guarded poisoning; `dispatch.py` treats `SANDBOX_UNAVAILABLE` as retryable ($\le 1500$ lines); `product_checks.py` and Feature 003 spec require `@Override inject(TestInjector)` and owned-role cleanup; tests pass (888/888 demo, 33/33 repo).
- Next: catalog refresh and Feature 003 integration.
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

## Feature 003 Root Cause Debug & Handover Resilience — RESOLVED

- Owner decision: debug why Haiku failed in 3 sessions on Feature 003, preserve reasoning effort 'max', make system resilient against handover traps, and enable reliable relaunch of 003.
- State:
  - Root cause confirmed: in build `557785d03d5f`, Haiku's code changes had fully passed checks (`check.status: passed` at 18:09:37 in session 1). However, fresh handover sessions (2 and 3) initialized in-memory `lastCheck` as `null` because `runner.py` did not pass handover check state to Flue. `finishReminder(null)` forced the model to keep working with `"You have not run run_protected_checks"`. Combined with unguided post-check file edits under reasoning effort `max`, each session hit the 250k context token ceiling (`gate.closed`), exhausting 3 sessions. Furthermore, `flue_builder.py` did not snapshot into `retained` upon normal handover and did not include `handover_limit` in candidate recovery.
  - Fix: `runner.py` passes `AEION_HANDOVER_CHECK` to Flue so resumed sessions preserve passed check state; `factory-checks.ts` initializes `lastCheck` from `AEION_HANDOVER_CHECK` and returns explicit completion instructions upon passing; `flue_builder.py` updates `retained` on each handover and recovers candidates on `handover_limit` (also reflected in `store.py`).
  - Verification: 30/30 Flue tests pass, 9/9 work limit tests pass, 33/33 repo unit tests pass, repo-health passes.
- Next: restart Feature 003 build on cockpit / factory daemon.
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

## Factory 3.0 Modernization Plan (All 4 Pillars) — MERGED TO MAIN

- Owner decision: keep thinkingLevel 'max' everywhere across all roles, make system resilient against failure modes, implement OpenShell 0.1.8 qualification and bridge I/O caching, Flue 2.3.0 persistent state and passed-check finish steering, Hindsight 1.2.1 SDK integration with cognitive synthesis fallback, and Langfuse v5.2 enterprise prompt management and multi-dimensional evaluation scores.
- State:
  - Pillar 1: OpenShell 0.1.8 pinned with binary sha256 and OCI image digests (`ghcr.io/nvidia/openshell/sandbox:0.1.8`, `supervisor:0.1.8`); `demo/app/bridge.py` in-memory read cache with mutating invalidation (`write`, `mkdir`, `rm`, `exec`) eliminates subprocess overhead; `demo/app/sandbox.py` supports both 0.1.7 and 0.1.8.
  - Pillar 2: `hindsight-client==1.2.1` pinned; `demo/factory/live_context.py` implements `reflect_cognitive_synthesis` with graceful fail-closed fallback to recall when the provider is `none`.
  - Pillar 3: `demo/flue/src/agents/coder.ts` tracks execution phase, checks run, and last check status via `usePersistentState`; upon passing `run_protected_checks`, steers the model to submit feedback and conclude without unrequested refactoring or handover exhaustion.
  - Pillar 4: `demo/factory/prompts.py` centralizes system prompts for author, reviewer, and preparer with deterministic local templates and Langfuse Prompt Management fallback; `demo/app/scores.py` computes multi-dimensional scores (`factory.check.acceptance`, `factory.review.consensus`, `factory.budget.efficiency`, `factory.cache.hit_ratio`) without polluting synthetic demo verification.
- Next: catalog refresh for next features on main (who: agent).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [docker demo](../knowledge/components/docker-demo.md).

## Feature 002 PostgreSQL migration and SQLite cutover — MERGED

- Owner decision: calibrate review output tokens to 32k for reasoning models within $1.00 USD cost cap, enforce concise review prompts, add test fixture attribution guardrails, fix SAST SQL format warnings in `DatabaseOperator`, and inject Optional datasource URL for databaseless boots.
- State: Build `d47014cbfad44b5190ec3c8d1b5130e3` completed Docker product checks, passed review circuit (GLM-5.3-Flash and Minimax-M3.1-Flash approvals), opened PR #18 on `OualidGuennif/aeion-autonomous-forum`, passed all 6 GitHub Actions CI checks (`Product artifacts` with 89 tests on PostgreSQL 17, `sast-scan` with 0 findings, `Knowledge/links`, `dependency-scan`, `secret-scan`, and `Architecture refresh`), merged autonomously into `main` (commit `ae0bd57d00897e3145fb8e51da76725380e7409a`), and recorded integration in `feature_integrations` with status `merged`. Cockpit daemon active on port 8088.
- Next: catalog refresh for next features (003 PostgreSQL testing fixture, 013, 014) on main.
- Blocker: none for Feature 002.
- Evidence: [validation](validation.md); https://github.com/OualidGuennif/aeion-autonomous-forum/pull/18 .

## Builder check diagnostics, signature streak and round continuation — MERGED

- Owner decision: make live builders see structured JUnit failure diagnostics, stop only on repeated identical failure signatures after baseline reproduction, use correction rounds on `repeated_check_failure`, seed the cleanest validated candidate on a relaunch of the same base and spec, enforce repo-health comment block bounds ($\le 20$ lines) locally before publication, include `Docs-Checked` architecture spec trailer in automated forge commits, and reconcile orphan budget reservations automatically.
- State: `_junit_failures` enriches `failed_tests` from JUnit XML, `note_check_failure` tracks `(reason, failed_tests, compiler_errors)` with a 5-check streak after skipping untouched baseline reproduction, `next_step` advances through correction rounds on `repeated_check_failure`, `prior_candidate` seeds the cleanest validated candidate on same-base/same-spec relaunch, `run_protected_checks` and `review` deterministically refuse comment blocks over 20 lines (repo-health), `demo/factory/github.py` generates the `Docs-Checked` architecture trailer, DailyBudget settles reservations cleanly and reconciles orphan reservations on boot, native qualification is active (`Ready: True`), and Feature 001 build `a27fb24c324b` is merged autonomously into `main` (PR #17, commit `aebcc9be9c4728fc74e1f09e86318f6a677632b7`) with all 6 checks green.
- Next: catalog refresh for next features (002, 003, 013) now that 001 is integrated on main.
- Blocker: none for Feature 001.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); https://github.com/OualidGuennif/aeion-autonomous-forum/pull/17 .

## Ghost PR evaluation archive, claude-mem decommission, Hindsight 1.2.0, Arbiter & Live Context — COMPLETED

- Owner decision: safely archive open ghost PRs into Hindsight as failure evaluations, delete remote branches, decommission redundant claude-mem in favor of deterministic local verified checkpoints, upgrade Hindsight to 1.2.0 with RRF reranking, implement an intelligent Model Arbiter & Re-ranker via Flue-Pi Tier 1 (`flue-just-bash` in-memory), and create a sanitized Live Context loop injecting failure constraints into builder prompts.
- State: PRs #7–#14 archived into bank `aeion-demo-real` (tags `postmortem`, `failure-eval`) and closed with branches deleted (0 open PRs, only main/develop remain). `claude-mem` removed; working checkpoints verified locally. Hindsight 1.2.0 active with RRF reranker. `demo/factory/arbiter.py` arbitrates model selection with empirical scoring and Tier-1 classification, failing closed. `demo/factory/live_context.py` injects bounded sanitized constraints. Full demo test suite (868/868) and repo health pass.
- Next: catalog refresh and admission of Feature 002.
- Blocker: none.
- Evidence: [validation](validation.md); [docker demo](../knowledge/components/docker-demo.md); [arbiter](../demo/factory/arbiter.py); [live context](../demo/factory/live_context.py).

## Trusted product CI and PostgreSQL/React — PARTIAL

- Owner decision: workers may propose dependency transitions without changing their evaluator; trusted CI updates use separate publisher/release credential roles.
- State: product CI PR 5 is merged as `e55b820ca4534738283df1674ba80be43ec03fa5` with all six exact-head checks green. Observer adapters 001/002/014, isolated unit PostgreSQL 17, migration/import/restore and frozen React build/test are implemented and natively qualified.
- Next: implement product 014 React and 002 PostgreSQL through actual workers after 001 integration (who: agent).
- Blocker: qualified adapters and CI are not implemented product migrations or deployed React; preserve canonical checkout and local data.
- Evidence: https://github.com/OualidGuennif/aeion-autonomous-forum/pull/5 ; [maintainer tool](product-ci-adapters-2026-11-05/maintain.py).

## Actual environments and cockpit links — OPEN

- Owner decision: provide real staging/production links and readable implementation stages; technical-only features may explicitly have no dedicated demo.
- State: the cookie-filtering product proxy is tested locally; the cockpit shows Staging and Production as "Not deployed yet" and omits the synthetic canary drill.
- Next: wire checked product artifacts to isolated environments, prove readiness and exact source identity, then expose verified links (who: agent).
- Blocker: no real staging or production deployment receipt exists yet; do not relabel the unverified local container as delivered main.
- Evidence: [Cockpit contract](../knowledge/components/operator-cockpit.md); [product proxy](../demo/factory/product_proxy.py).
