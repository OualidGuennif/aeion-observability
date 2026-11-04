# Current work

Updated 2026-11-03, Europe/Paris. Read this first; older HANDOVER blocks are historical. This checkpoint records verified delivery separately from unfinished work. All repository documentation stays in English.

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
- Blocker: The observer workspace contains extensive uncommitted tracked/untracked work. Do not use a broad add-all or treat a clean tracked diff as proof that new artifacts were included. No original forum volume/database was migrated, reset or deleted.
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

## Observability backlog and main synchronization — AUTHORIZED, PENDING

- Owner decision: Merge all approved aeion-observability work into main after verifying it is clean and ready; no force-push or protection bypass.
- State: Last fetched observer develop/HEAD/origin-develop is 786e3ff47f26fa960c2c705de18f9d2d07155457. origin/main is ca9532a0edd4a8c46eb6cd4244fdfffd2925ef64: develop is 76 commits ahead and zero behind, plus the current uncommitted factory/catalog/cockpit work. No observer PR was open at the last read. Main enforces admins and strict required docker-demo/offline-examples checks.
- Next: Agent finishes supported functionality, inventories tracked/new/deleted files without secrets, records exact-head independent review, pushes the approved delivery, waits for current required CI and confirms protected main. Re-fetch refs/protection before that action.
- Blocker: No observer commit, push or merge has been performed for this delivery. Product PR 4 is a separate repository result. Do not describe the 76-commit backlog as integrated while this entry is pending.
- Evidence: Configured git/gh read-only metadata checks, [handover](HANDOVER.md), [validation journal](validation.md), and the PR/sign-off rules already read for the authorized scope.

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
- State: Latest complete public-source snapshot /tmp/aeion-full-pass-20261102-al7jqp3u passed678demo tests (7 explicit dependency/environment skips),33examples,19Flue and16cockpit-client tests. After that snapshot, the shallow-clone correction passed the30focused tests listed above and real canonical-source readback. Full suite was not rerun for this last correction. Last journal read: forum$0.30 settled/$14.70 remaining; observer$0/$15. No paid review was active at that read.
- Next: Agent runs checks proportionate to new behavior, then final required CI after assembling the complete approved delivery. Re-read live budget/expiry/leases before any actual new model dispatch. Never inspect raw transcripts, .env, auth files, process environments or credential dumps.
- Blocker: Provider-usage costs are estimates/resource accounting, not invoice reconciliation; unknown costs cannot become zero. Do not reuse an expired lease or qualification receipt. No new scheduler or recurring replacement was created after the one-shot05:00 resume fired.
- Evidence: [Validation journal](validation.md), ignored v6/{check,ci-readback,telemetry-readback,source-sync-readback,materialization-readback}.json, focused unittest output and public-source snapshot path. Documentation checks are recorded separately from runtime qualification.

## Resume order and evidence locations — NEXT ACTIONS

- Owner decision: Finish the existing approved scope with the smallest robust changes, preserving all evidence and without another permission loop.
- State: Product baseline merge, native review transport, current-main synchronization/materialization and local control mechanisms are verified at the bounds above. Remaining implementation is the grader experiment, qualified PostgreSQL/React transition, real MD execution and product delivery, final cockpit, then reviewed observer integration/reload.
- Next: Agent: (1) reproduce grader boundary on exactmain; (2) qualify dependency/export/check adapters; (3) dispatch real isolated product work with two fresh independent reviews and protected CI/main; (4) validate actual deployed demo and cockpit steps; (5) review/publish/merge observer backlog plus new work; (6) reload safely and read back cockpit/telemetry. Keep current.md, HANDOVER and validation consistent after each result.
- Blocker: No blanket ready/optimized/security-complete claim is supported yet. Resolve concrete failed or missing evidence; never unlock by weakening tests, fabricating receipts or relabeling scripted runs. Preserve previous failures and original private data.
- Evidence: [HANDOVER](HANDOVER.md) retains detailed/historical continuity; [validation](validation.md) carries command/results; [bootstrap report](product-ci-bootstrap-2026-11-03/README.md), [plan](factory-flue-plan-2026-11-03.md), [factory contract](../knowledge/components/factory-flue.md) and [architecture](../demo/forum/ARCHITECTURE.md) provide the implementation/evidence map.
