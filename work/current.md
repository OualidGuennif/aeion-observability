# Current work

Updated 2026-11-04 verification checkpoint. Read this first; older HANDOVER blocks are historical. This checkpoint records verified delivery separately from unfinished work. All repository documentation stays in English.

## Repository regression and current main — VERIFIED

- Owner decision: Rerun all repository tests and check that the latest main code is present; preserve application/operator state.
- State: Fresh refs: HEAD/origin-develop10f072791a2378adad48789a91788c0d37bf0337; origin-mainae5a6ef1441a418402e42e61619424b11435a01c. Only current.md/validation.md differed before this pass; code matches main. Full demo683/0skips, examples33, Flue19, cockpit16, catalog21 and Factory pass. The15 native Deno/Graphify architecture tests cover all initially skipped cases. Hosted main has four green checks. OpenShell security/scenarios, all three Flue tiers, complete/unknown-cost reviews, PostgreSQL, Chromium, Java factory and automatic MD-preparation native fixtures all pass; the last uses four distinct allowed models and confirmed metadata readbacks.
- Next: Agent reports this completed regression pass; the open product roadmap remains qualified PostgreSQL/React transitions, real MD-to-main/product delivery, final cockpit/demo and operator activation. No code correction was required by this pass.
- Blocker: No unresolved regression failure. Initial snapshot-HEAD/local-product omissions and optional-tool skips were resolved as test setup; all final checks pass. A first native-preparation wrapper timed out at300s; its preserved cleanly retired attempt was followed by a fresh900s-wrapper run passing in205.44s, without changing engine limits. PostgreSQL template qualified=false and operator factory activation remains absent.
- Evidence: [Full test report](test-pass-2026-11-04.md); public snapshot/logs /private/tmp/aeion-tests-20261104-sm4buts3; fresh exact-main GitHub readback. All generator inference uses local scripted endpoints; native mechanisms do not establish product/model quality or deployment.

## Authorized outcome and working boundaries — ACTIVE

- Owner decision: Continue the approved factory/cockpit work autonomously, then push and merge all approved Observability changes into protected main after checks. No repeated questions while the owner sleeps. The latest request explicitly asks for a detailed current.md.
- State: Target outcome is 100 dependency-ordered MDs launchable from one cockpit, with durable stages, completed-feature locks, two independent approvals, PR/CI/confirmed main, and a verified product demo link where applicable. Keep Quarkus/Java, migrate SQLite to PostgreSQL, and use React DOM/TypeScript web; no mobile application.
- Next: Agent completes the open slices below, verifies actual behavior and updates this checkpoint after each meaningful result. Product implementation goes through dispatched Flue/Pi workers; Observability builds and supervises the factory, not a hand-edited product mirror.
- Blocker: Full product readiness is NOT established. PostgreSQL/React qualification, final cockpit delivery and Observability main synchronization remain open. Existing approval never authorizes bypassing protection, discarding operator work or claiming synthetic results as real.
- Evidence: [Implementation plan](factory-flue-plan-2026-11-03.md), [approved product architecture](../demo/forum/ARCHITECTURE.md), [ordered catalog](../demo/forum/features/README.md), and the latest owner instructions in this conversation.

## Workspace identity and protected operator state — PRESERVED

- Owner decision: Preserve all existing work, data, histories and budget liabilities; keep forum and Observability responsibilities separate.
- State: Observer root is /Users/wallseven/Desktop/AEion./aeion-observability, including the literal dot in AEion. Canonical product checkout is demo/.local/factory/agents/aeion-autonomous-forum. Its local HEAD remains a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb; origin/main is 63bdece8056136209e0e3d2e68dbf0879005fec9. demo/forum-app, forum-db and forum-mobile are read-only observer mirrors.
- Next: Agent uses immutable committed product bytes and disposable clones. Recheck actual process/ref state before reload or publication; do not reset, stash, clean, force-push or silently move the operator checkout.
- Blocker: The earlier extensive tracked/untracked delivery is now integrated by PR18. Working tree was clean at the start of this verification; this pass adds documentation only. Keep preserving operator files/data and do not confuse observer mirrors with writable product source.
- Evidence: Real source-sync and materialization readbacks in ignored demo/.local/factory/bootstrap/v6/; the latter confirms unchanged source HEAD, remote-main ref and complete porcelain status after a clean exact-main clone.

## Product bootstrap and protected publication — BASELINE MERGED

- Owner decision: Publish the existing committed backend plus trusted CI using isolated publisher/release roles, exact reviewed bytes and required GitHub checks; Workflows permission was explicitly activated by the owner.
- State: [Product PR 4](https://github.com/OualidGuennif/aeion-autonomous-forum/pull/4) is merged. Reviewed head 932c35252b83818e1db803987a589bfffb4964; confirmed merge/main 63bdece8056136209e0e3d2e68dbf0879005fec9. Bundle v6 contains 51 files/198356 bytes, SHA256 6d56126eb021ea98a4448789a68d292d05f4e0267d5515275b6eac7603ccf04d. All five required checks plus Graphify/Archify passed; optional review was skipped and was not counted as a pass.
- Next: Agent uses this protected main as the next frozen product base. Keep obsolete PR 3 closed and its v5 attempt cancelled/fenced, with the old branch, votes, failures and immutable bundle retained.
- Blocker: This is an import of the existing SQLite backend and CI. It does NOT implement PostgreSQL, React, all 100 features, or a verified product deployment. A merged PRODUCT PR does not mean OBSERVABILITY main is up to date.
- Evidence: [Bootstrap report](product-ci-bootstrap-2026-11-03/README.md); ignored v6/remote.json, check.json, ci-readback.json and v5/superseded.json. Local CI included actual isolated Gradle test/quarkusBuild and documentation checks against the actual base diff.

## Actual independent votes and telemetry — READ BACK

- Owner decision: Two approving reviewer families must differ from each other and from builder/preparer; send only approved bounded source for review, with metadata-only observability.
- State: Fresh v6 GLM and Qwen votes approved the exact 51-file bundle; old GLM/DeepSeek votes were not reused after bytes changed. GLM: run 6f676bb5416648ba9488d610114ea749, trace 3981e6d8d34863839b823d8b7310350b, 3 requests, total input151910/output7679, resourceUSD0.02000821. Qwen: run 8a340347a2dc4ebea82f78699df893f0, trace c7d24c2ec34bd24b59e8a06a094a5964, 4 requests, total input223982/output8918, resourceUSD0.04935952. Totals across requests are not peak context sizes.
- Next: Agent retains per-attempt accounting and independently reads back future role outcomes. Routing compares only matching real task/check/runtime/profile cohorts, with explicit cold-start priors and no synthetic ranking evidence.
- Blocker: These two approvals certify this exact baseline packet, not future features or general model superiority. Resource estimates are not additional bank invoices. Recalled memory, traces and model votes cannot grant permissions or override checks.
- Evidence: Ignored v6/telemetry-readback.json confirms Langfuse generation counts and exact Hindsight documents; claude-mem execution checkpoints were also read back. [Telemetry contract](../knowledge/operations/telemetry-contract.md) and [Flue factory contract](../knowledge/components/factory-flue.md).

## Observability backlog and main synchronization — MERGED TO MAIN

- Owner decision: Merge all approved aeion-observability work into main after verifying it is clean and ready; no force-push or protection bypass.
- State: PR #18 merged to main as commit `ae5a6ef1441a418402e42e61619424b11435a01c` after all required CI checks (docker-demo, offline-examples, doc-links, knowledge-check, architecture-refresh) passed green. Post-merge CI and Architecture refresh workflows on origin/main passed green. develop synced with origin/main at commit `4557d1463640aa0d9dfe76328232b941f6e579a9` (trees are byte-identical, zero diff).
- Next: Proceed with remaining factory roadmap milestones (live product activation, PostgreSQL/React qualification).
- Blocker: Factory live product activation remains gated by product readiness.
- Evidence: [PR #18](https://github.com/OualidGuennif/aeion-observability/pull/18), main commit `ae5a6ef`, develop sync commit `4557d14`, green CI runs 41798358482 and 41798806347.

## Execution, isolation and recovery — IMPLEMENTED LOCALLY

- Owner decision: Use Flue/Pi with OpenShell tier 3; do not trust LLMs. Only GLM 5.3 Flash, DeepSeek V4.1 Flash, Qwen 3.8 Flash and Claude Haiku 5.5 medium may start workers. Preserve the hard $15/day purse.
- State: Direct model engine removed. Untrusted workers receive no host mount, key, socket or free network authority. Separate preparation freezes MD/architecture/base/scopes; two reviewer families exclude author/preparer. Durable PR/CI/main continuation uses separate build/read, publisher, release and inference processes. Lease/generation checks fence stale completion, later model requests and publication staging; unknown external effects require reconciliation.
- Next: Agent completes actual PostgreSQL/React activation and end-to-end product execution through these existing roles. Keep authority in deterministic supervisor code and complete-artifact receipts.
- Blocker: Activation marker demo/.local/data/factory-flue-qualification.json remains absent; the controller has not been reloaded for this delivery. Last previously observed PID11582 is historical and must be rechecked. No silent fallback to the retired direct engine is allowed.
- Evidence: [Factory trust model](../demo/factory/trust-model.md), [execution contract](../knowledge/components/factory-flue.md), tests for isolation, recovery, publication state, vote integrity and qualification. No assistant subagent or replacement schedule was created; the unique05:00 continuation already fired and was deleted.

## Context admission, review bounds and unknown costs — VERIFIED LOCALLY

- Owner decision: Let approved models launch; do not block Qwen on a Unicode byte estimate falsely presented as exact tokens. Retain accounting, context continuation controls and the existing daily ceiling.
- State: Profileversion flue-openshell-v4 separates changed cohorts. Qwen/Haiku use provider-usage-v1: byte bounds reserve cost only, complete API usage including cached input gates continuation; unknown usage stops, native input250k hands over, input+output above300k fails. Pinned tokenizers keep preflight. Complete factory review admits 240000 UTF-8 bytes, $1, 65536 output and 900s. Author export admits32files/250000bytes, max100000bytes/file; scopes and evaluator protections remain unchanged.
- Next: Agent retains reservations for unfinished/unknown cost and settles finalized unused liability. Reviews reserve their actual declared cap; preparation/authoring/review cannot continue on missing usage even if a model submitted approval.
- Blocker: There is no independent first-request300k preflight guarantee for closed-tokenizer Qwen/Haiku. Do not restore the old false340k byte-derived refusal or interpret request totals as a context measurement. Higher packet/output limits do not authorize new paths or paid automatic retry.
- Evidence: Context/cache/accounting regressions failed before correction and now pass; actual Qwen complete198KB review succeeded. Native Flue/Pi positive170062-byte review and missing-final-cost refusal also passed with scripted local APIs, exactly2requests each and zero real provider calls.

## Fresh main, MD preparation and shallow materialization — ROOT CAUSE FIXED

- Owner decision: Prepare a task automatically from its MD and current protected product main while preserving the operator checkout and separating credentials.
- State: New source.py subprocess loads only the build/read key, fetches fixed product main into a unique temporary ref, validates ancestry and conditionally updates origin/main. Real readback preserved local HEAD/worktree. Preparation discovers committed HTTP interfaces by @Path rather than Resource/Health filenames, including MigrationRunner /api/schema. The later base_checkout_failed was reproduced: a shallow source retained new main only in a remote-tracking ref, omitted by clone. Target.materialize now locally fetches the exact missing frozen SHA before checkout, without branch/FETCH_HEAD updates.
- Next: Agent resumes the native grader investigation on the now-materializable main, then verifies automatic preparation against the actual qualified product adapter. Preserve the diagnostic distinction between source synchronization and full feature execution.
- Blocker: The clone failure is fixed, but this does not qualify PostgreSQL/React acceptance or the full MD-to-merge path. Fetch failure deletes only the incomplete disposable clone and exposes base_fetch_failed, never raw private diagnostics. Source/target modules participate in the activation protocol hash.
- Evidence: New shallow/dirty-source regression failed before the fix and passes after; fetch-failure cleanup is covered. Focused checks:10target+11preparation+5source-sync+4qualification=30PASS. Real v6/materialization-readback.json confirms exactmain63bdece, a clean clone and unchanged source HEAD/ref/status; no model call or remote write.

## Frozen dependency admission — MECHANISM READY, NO ACTIVE TRANSITION

- Owner decision: A worker may propose required PostgreSQL/React dependency changes but must never modify the program that verifies them.
- State: FrozenBuild optionally binds exact SHA256 dependency bytes for only demo/forum-app/build.gradle, demo/forum-web/package.json and demo/forum-web/package-lock.json, each inside frozen scopes. Unknown paths, malformed/empty hashes and out-of-scope changes refuse. Approved hashes affect the frozen digest; historical receipts omit the optional absent field and remain readable. Default dependency-manifest denial remains for everything else.
- Next: Agent qualifies and explicitly registers the bounded PostgreSQL/web transition profiles, their frozen manifests, public tool/cache admission and independent product checks. Bind any admitted transition data into qualification identity before use.
- Blocker: No actual PostgreSQL or React transition currently registers an approved dependency policy. A mechanism unit test is not dependency resolution, migration qualification or authority for an arbitrary worker manifest. Deletion/rename export is also unsupported; never fake deletion with an empty file.
- Evidence: Three dependency-policy regressions plus review/pipeline tests pass. Candidate data lives in demo/factory/transitions/postgres/ with qualified=false. [Transition acceptance architecture](../demo/forum/ARCHITECTURE.md) and [factory execution inputs](../knowledge/components/factory-flue.md#inputs).

## PostgreSQL product transition — UNQUALIFIED

- Owner decision: Replace SQLite with PostgreSQL while retaining product data, deterministic migrations and separate migration/application authority.
- State: Native disposable PostgreSQL17 transport proved random separate administrator/migration/app roles, DML success, refused app schema/role DDL and confirmed cleanup. New Gradle data candidate uses Quarkus BOM3.40.1, PostgreSQL JDBC, Flyway and its PostgreSQL module; SQLite remains only in import-job/test configurations. Base build SHA256 f7b21e65ca79d30bee41a3fc9ff7840f395f2dcaf3c0d4be250ea9099c3010c7; candidate6d7c42641b5fd59f4446e51bd6ecec1c7de4dde5aa8e9b0638536529321fb7fb.
- Next: Agent qualifies dependency admission and dispatches the product worker for actual schema/migration/import/restore work. Verify checksum/ahead-schema/concurrent-start/rollback vectors, ID/time/content/account/session preservation, audit-specific grants and disposable test-database separation; keep the original volume intact.
- Blocker: Candidate is data only, explicitly qualified=false: no product Gradle file changed, no new dependency cache warmed. Existing product main still runs SQLite/custom MigrationRunner. Transport isolation does not prove Flyway behavior, product import/restore or least-privilege audit permissions. Features001/002/003 remain held by the ordinary adapter.
- Evidence: [Feature002 migration contract](../demo/forum/features/002-postgresql-migration-and-sqlite-cutover.md), [feature003 test-harness contract](../demo/forum/features/003-test-harness-with-an-ephemeral-database.md), [PostgreSQL/Chromium security record](chromium-security-2026-11-03.md), and transitions/postgres/identity.json.

## React web and browser boundary — TO COMPLETE

- Owner decision: Deliver a web application with React DOM/TypeScript; no mobile application. Visual/functional completed features need a real usable test link.
- State: Pinned non-root checker image contains Java25, Node26, React19, TypeScript, Vite, Vitest and Playwright. Native Chromium sandbox, namespaces, Seccomp-BPF/TSYNC and denied external network passed; Yama protection is absent and recorded. Public dependency/tool provisioning is distinct from candidate execution. Production React assets must be served by Quarkus on the same origin.
- Next: Agent qualifies web scopes/export suffixes, production build and independent browser/API checks, then dispatches real product implementation. Check loading/error/empty states, escaping, navigation/forms and active Expo retirement; verify the deployed product commit before offering a demo URL.
- Blocker: Current FlueBuilder export/context adapter covers app/docs and a limited suffix set, not qualified TS/TSX/CSS/HTML web work. No actual React product production/browser/API acceptance or active Expo retirement was completed. A browser transport probe cannot certify UI features or product deployment.
- Evidence: [React shell014](../demo/forum/features/014-react-browser-application-shell.md), [accessible navigation018](../demo/forum/features/018-accessible-react-navigation-and-forms.md), [Chromium qualification](chromium-security-2026-11-03.md), and demo/factory/checker-tools/ pinned public tooling.

## Protected grader boundary — REPRODUCED AND HARDENED

- Owner decision: Candidate code must not control its evaluator; all acceptance remains independent and deterministic, with no host key/socket/egress exposed.
- State: Native exact-main (`63bdece8056136209e0e3d2e68dbf0879005fec9`) baseline ran `FactoryBoundaryProbeTest` inside `DockerCheckRunner` and failed as expected (`returncode: 1`, `failure_kind: tests_failed`, `contract_assertion_failures: 1`). Candidate `CandidateInterceptor` (`InvocationInterceptor.interceptTestMethod -> invocation.skip()`) plus `META-INF/services/org.junit.jupiter.api.extension.Extension` and `junit-platform.properties` in candidate write scopes bypassed the unhardened check (`returncode: 0`, XML `tests=1 skipped=0 failures=0 errors=0`) while `FactoryBoundaryProbeTest.java` stayed untouched. `agent_files.py`, `artifact.py` and `checks.py` now refuse `META-INF`, `junit-platform.properties`, JUnit extension/platform hooks, foreign packages in `local/aeion/forum/` and skipped/unreported contract XML results (`builder_grader_tampered`, `grader_tampered`, `contract_not_executed`).
- Next: Agent retains this grader boundary across all prepared/pinned Java checks and applies equivalent evaluator-separation guards when qualifying React web and PostgreSQL transition checks.
- Blocker: This hardens the JUnit/Quarkus check boundary; it does not by itself qualify PostgreSQL migrations or React browser checks.
- Evidence: [Flue factory contract](../knowledge/components/factory-flue.md#invariants), `test_factory_target_check.py`, `test_factory_live.py`, and native `DockerCheckRunner` probe verification (`parse_error: builder_grader_tampered`, `reason: grader_tampered`).

## Cockpit stages, dependency queue and demo links — OPEN DELIVERY

- Owner decision: One understandable cockpit must launch supported MDs, prevent selecting already implemented features and show what is happening without an unexplained Needs setup label.
- State: Existing local work includes catalog sequence, availability/locks, exact blockers and MD preview, generation-checked progress and durable publication/reconciliation state. Required end state shows queued/dependencies → preparation → authoring → checks → two reviews → PR → CI → merged → deployment/demo, with persisted progress across reconnect/restart. Completed identity must match current spec and a real confirmed merge.
- Next: Agent completes deterministic prerequisite admission/wakeup, usable filtering/selection, stage/evidence links and authenticated browser verification. Derive demo URLs only from trusted routes plus verified deployed release metadata. For technical work render exactly: Technical feature, no specific demo available.
- Blocker: Final all100 supported-dispatch qualification, final UI/browser validation and real post-merge product/demo delivery are not complete. Do not mark all100 ready or a feature deployed from a synthetic receipt, a proposed URL, or an old spec implementation.
- Evidence: [Cockpit component](../knowledge/components/operator-cockpit.md), [catalog](../demo/forum/features/README.md), progress/admission/client/store tests and the earlier dated fixture screenshot; a fixture screenshot is not the live authenticated acceptance result.

## Verification, budget and scheduling checkpoint — RECORDED WITH LIMITS

- Owner decision: Keep the daily forum purse at $15, retain failed attempts and unknown liabilities, and report actual checks without presenting synthetic probes as real end-to-end success.
- State: Current public snapshot /private/tmp/aeion-tests-20261104-sm4buts3 passed683demo tests/0skips,33examples,19Flue,16client,21catalog and Factory;15 native Deno/Graphify query cases also pass. All native checks, including full Java factory276.94s and automatic Java preparation205.44s, pass. Native generator endpoints are scripted locally; four allowed models and independent roles are mechanism fixtures, not measured provider quality. The old forum$0.30/$15 balance is historical; no new operator balance/invoice claim is made.
- Next: Agent keeps the dated report and failed/skip attempts, then follows the remaining product roadmap if resumed. Re-read actual operator budget/expiry/leases before any future paid dispatch; this test pass does not activate product launches.
- Blocker: Provider-usage costs are estimates/resource accounting, not invoice reconciliation; unknown costs cannot become zero. Do not reuse an expired lease or qualification receipt. No new scheduler or recurring replacement was created after the one-shot05:00 resume fired.
- Evidence: [2026-11-04 test report](test-pass-2026-11-04.md), per-suite logs/exit codes and exact-main GitHub readback under /private/tmp/aeion-tests-20261104-sm4buts3. Earlier bootstrap and snapshot evidence remain historical, not substituted for the new checks.

## Resume order and evidence locations — NEXT ACTIONS

- Owner decision: Finish the existing approved scope with the smallest robust changes, preserving all evidence and without another permission loop.
- State: Product baseline merge, source synchronization/materialization, the reproduced-and-hardened JUnit boundary and observer PR18/main integration are complete at the documented bounds. The present regression pass verifies that code; remaining product delivery is qualified PostgreSQL/React transitions, operator activation, real MD-to-main/product execution and final cockpit/demo behavior.
- Next: Agent: finish this test report first; then qualify PostgreSQL/React dependency/export/check adapters, dispatch isolated product work with two fresh independent reviews and protected CI/main, validate deployed product/demo and cockpit steps, and activate/reload only with the required real evidence. Keep current.md, HANDOVER and validation consistent. Do not repeat the already-completed observer PR18 merge or JUnit reproduction as pending work.
- Blocker: No blanket ready/optimized/security-complete claim is supported yet. Resolve concrete failed or missing evidence; never unlock by weakening tests, fabricating receipts or relabeling scripted runs. Preserve previous failures and original private data.
- Evidence: [HANDOVER](HANDOVER.md) retains detailed/historical continuity; [validation](validation.md) carries command/results; [bootstrap report](product-ci-bootstrap-2026-11-03/README.md), [plan](factory-flue-plan-2026-11-03.md), [factory contract](../knowledge/components/factory-flue.md) and [architecture](../demo/forum/ARCHITECTURE.md) provide the implementation/evidence map.
