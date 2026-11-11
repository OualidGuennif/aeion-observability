# Current work

Updated 2026-11-11. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Modernization Phase 1 and Max-Thinking Resilience — IN PROGRESS

- Owner decision: keep thinkingLevel 'max' everywhere, expand output tokens to 65k, make preparer resilient with model substitution, cache bridge metadata, and adopt native OpenShell and Hindsight SDKs.
- State: openshell 0.1.8, hindsight-client 1.2.1, and langfuse 5.2.0 installed; max_output_tokens calibrated to 65536 in preparation and execution; TaskPreparer retries across distinct model families; SandboxBridge caches stat/exists/readdir metadata; native Hindsight client wired with clean closure; admission proof activated; Feature 003 correction contract reuse verified in Round 2; Attempt 2 building with Qwen 3.8 Flash.
- Next: monitor Feature 003 preparation, authoring, and review through publication (who: agent).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

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
