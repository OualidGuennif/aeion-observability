## Builder check diagnostics, signature streak and round continuation — 2026-11-09

- Feature 001 launch on reloaded controller (`PID 10582`, PR 36 merged as `3c547112ad8e226be9384a029476a630e6ca87b3`) avoided `RequestValidationFilter.java` across all three attempts (`c0a0fd3430d5`, `919df210ccd5`, `0b14e772f599`) and converged to 16 scoped files with one remaining unit test failure (`ForumHealthTest > theSchemaLedgerRefusesWithoutADatabase() FAILED`), but stopped at `attempt 3 of 3 · round 0 of 2` because `note_check_failure` counted three coarse `product_unit_tests_failed` reasons (including baseline reproduction), `_failed_tests` omitted the JUnit XML assertion message (`Expected status code <503> but was <200>`), and `repeated_check_failure` skipped correction rounds 1 and 2 as a crash.
- `demo/factory/checks.py` and `demo/factory/product_checks.py` now enrich `failed_tests` from JUnit XML (`_junit_failures`) with bounded exception class, candidate `file:line` and structured comparison tokens, and document Quarkus `QuarkusTestResourceLifecycleManager` (ordinal 400) vs `QuarkusTestProfile` (ordinal 275) in Feature 001 instructions. `demo/factory/flue_builder.py` and `demo/factory/dispatch.py` track the full failure signature `(reason, failed_tests, compiler_errors)` with a 5-check threshold after skipping the initial untouched inherited baseline check, advance through correction rounds on `repeated_check_failure`, and seed the cleanest validated candidate on a fresh launch of the same base and spec (`prior_candidate`). `demo/forum/tools/generate_features.py` emits `demo/forum/features/TEMPLATE.md` and verifies all 100 feature specs (`001`..`100`) carry all eight sections, three delivery steps, and required write paths.
- Checks: `python3 -m unittest demo.tests.test_factory_target_check demo.tests.test_factory_work_limits demo.tests.test_factory_correction_rounds -v` (61 OK), `python3 demo/forum/tools/generate_features.py --check`, `python3 -m unittest discover -s demo/forum/tools -v` (21 OK), `tools/knowledge/knowledge-check`, `tools/knowledge/doc-links`, and `tools/repo-health/repo-health` passed (`dispatch.py` is 1,499 lines).

## Out-of-scope Spec doc guard and review fixes — 2026-11-09

- Inspected held build `39db9530e56d495295b002c0f1111b75` (`RequestValidationFilter.java` diff against base `e55b820ca4534738283df1674ba80be43ec03fa5`): the author replaced `// Spec: knowledge/components/request-validation.md` with `// Spec: knowledge/components/agora-product.md` and `// Docs-Checked: knowledge/components/request-validation.md` while adding `Origin`/`Referer` header normalization. Because `knowledge/components/request-validation.md` is outside Feature 001 `write_scopes`, product PR 11 failed `tools/knowledge/doc-links` Rule L3.
- `demo/factory/flue_builder.py` and `demo/factory/dispatch.py` now check both candidate and base `Spec:`/`Docs-Checked:` headers against `write_scopes`, refuse out-of-scope Spec edits as `BuilderError('knowledge_doc_outside_scope')`, and instruct the author in `baseline_note`, the build prompt and `CI_REPAIRS` to revert that code file.
- `demo/app/telemetry.py` moves OTLP `/v1/logs` export onto a bounded background queue (`maxsize=1024`), `demo/factory/routing.py` bumps `METHOD = 'flue-factory-routing-v6'` with `treatment_digest()`, `demo/factory/execution.py` formats live budget ceilings with two decimal places (`50.00`, `1.00`) and `test_factory_execution.py` isolates `AEION_*_USD` environment overrides, `demo/app/kpis.py` and `demo/app/selection.py` require explicit integer `human_interventions == 0` and complete maturity for autonomous success (`autonomy_basis: passed_checks_no_reported_intervention`), and `README.md` / `demo/app/index.html` align displayed ceilings, context policy and best-effort export semantics.
- Checks: `python3 examples/compare_cohorts.py`, `python3 examples/validate_fixtures.py`, `python3 -m unittest discover -s tests -v` (33 OK), `npm --prefix demo/flue test` (29 pass), targeted and full `demo/tests` suites, `tools/knowledge/knowledge-check`, `tools/knowledge/doc-links`, and `tools/repo-health/repo-health` all passed (`dispatch.py` is 1,500 lines).

## Feature 001 stops on the same knowledge rule — 2026-11-09

- Product pull requests 7 through 11 stay open. Each fails Knowledge, links and repository health. Product artifacts succeeded. Pull request 11 names RequestValidationFilter.java and does not name knowledge/components/request-validation.md.
- Feature 001 write paths include demo/forum-app/ and exclude that knowledge document. A read-only query showed the latest feature 001 row as build 39db9530e56d, status held, hold owner_review_required. The earlier relaunch 97eff0a3a37e4861ade9e52e8b7dc7d1 is no longer the latest row.
- The factory repair still tells the author to update the owning knowledge document. No factory change for that loop is committed. The Java diff of the filter was not read in this closure. Do not merge those product pull requests. Do not widen the write scope. Do not relaunch feature 001 from this note. The native claude-security plugin was not run.

## The author loop stops after three identical checks — 2026-11-08

- Pull request 35 merged as 4fd3e9c766d82402b65df306cdd8d6a0581d0aa1. Architecture refresh on that main SHA succeeded. Controller PID 38846 replaced 89596 and listens on 127.0.0.1:8088. Admission exited 0, status qualified, activated true, product delivery not claimed, ready true. Feature 001 was then admitted as build 97eff0a3a37e4861ade9e52e8b7dc7d1 and was dispatched. Features 002, 003 and 013 stay catalog_changed.
- Independent review of d6aea62 was NOT OK: a local follow-up whose previous usage row was incomplete still checkpointed as AEION_HANDOVER when the local count no longer fit. That test failed with AEION_HANDOVER. The same follow-up is now USAGE_UNKNOWN, with no checkpoint.
- Pull request 35 CI failed on the builder-error receipt (`KeyError: forwarded_count`), on two settlement sends (`[200, 409, 403]` instead of `[200, 200, 409]`), and an identical finished failure left `draft_failures` at 1. Those three tests failed before the fix. The receipt now keeps the execution diagnostics and the check. An identical finished failure increments the draft count without a second progress event. An incomplete usage row blocks a grown handover only; an ordinary follow-up keeps the reservation. `cd demo && python3 -m unittest` of the dispatch diagnostic, the store repeat, settlement and context admission: 28 OK. The full `discover -s tests` was 851 tests with one local failure in `test_factory_execution`: `cost_reservation_usd` was `50` rather than `50.00` when the process carries an author-ceiling override. That assertion is outside this diff. dispatch.py is 1500 newlines. store.py is 1498. The native claude-security plugin was not run. knowledge-check passed. doc-links against origin/develop passed, 153 links.
- Feature 001 build 0e02148b89f3 was cancelled. A read-only count showed no dispatched, queued, gated, pr_open or approved build.
- The missing complete round was the open author stage. A failed protected check did not stop the model, and the test names were dropped before the next decision. Preparation's startup refusal stays the expected negative control.
- Three identical reasons now set repeated_check_failure on the next admission. Check evidence and progress keep at most eight pattern-checked names. A Gradle task or exception class is kept when no test line exists. An unexpected follow-up exception is RELAY_FAULT. A running protected check is not a stall. The cockpit shows admission hours and does not renew the proof.
- minimax-m3.1-flash replaces mistral-large-4. Prices stay the pinned Go rates 0.15/0.60/0.015 and context 1000000. budget_multiplier 4 is the highest measured Go multiple, an upper bound, not a measured MiniMax rate. No effort map is sent.
- Checks this session: the touched demo unit modules passed (143), and the cockpit client, provider and factory-checks node tests passed (41). knowledge-check passed. doc-links against origin/develop passed, 153 links. VERSION stays 1.9.0. Feature 001 was not relaunched.
- Controller PID 74366 was replaced by PID 89596 after an identity check. Admission exited 0, status qualified, activated true, product delivery not claimed, ready() true. The native claude-security plugin was not run.
- Independent review of b055f63 was NOT OK: a truncated upstream chunk became RELAY_FAULT after the claim and before its usage row, so a later finish was USAGE_UNKNOWN. The two new context-admission tests failed on that code with RELAY_FAULT. A truncated chunk is now TRANSPORT_ERROR, the claim stays open, and the session does not continue.
- Independent review of cd48926 was NOT OK: a 257-message follow-up after a usage row with no cost returned AEION_HANDOVER before the usage gate. That test failed with AEION_HANDOVER. The same follow-up is now USAGE_UNKNOWN, with no checkpoint and no second provider call.
- Independent review of 69191a6 was NOT OK on two points. A cached failure did not replace the published check, so the source assertion for `runtime.last_check = cache[digest]` failed. A passed check with reason `check_failed` was told to the next author as a failure. The cache hit now publishes that check, and correction text requires status failed.
- Independent review of 343f594 was NOT OK. A passed gate still replayed a stale self-check, and only one `protected_check.finished` call existed, so the three-failure cockpit count stayed at 1. Those three tests failed before the fix. A passed gate is now skipped, and cached and raised failures emit the finished event.
- Independent review of 89c29cf was NOT OK: skipping a newer passed gate still returned an older failure of the same spec. That test failed with the older test name. The newest passed gate now returns no failure.

## A grown session hands over — 2026-11-08

- Build 9d7d4952c034 used three sessions and stopped on handover_limit after saving 16 candidate files. Build 48374a71be8c ran one session, 100 forwarded requests, usage complete, 21 protected checks failed as product_unit_tests_failed, retained 15 files, then stopped on CONTEXT_UNKNOWN. No further attempt was admitted. A follow-up with more than 256 messages now closes as AEION_HANDOVER. `cd demo && python3 -m unittest tests.test_context_admission` : 10 OK. PID 62409 was replaced by PID 74366. Admission exited 0, status qualified, activated true, product delivery not claimed, ready() true. Feature 001 was not relaunched.

## Controller reloaded onto the path note — 2026-11-08

- PID 29673 was stopped after an identity check, with no build in dispatched, queued, gated, pr_open or approved. PID 62409 started in live mode and listens on 127.0.0.1:8088. Admission exited 0, status qualified, activated true, product delivery not claimed, ready() true. Feature 001 was not relaunched.

## A correction names the changed paths — 2026-11-08

- The knowledge correction listed no file, and a protected check that raised became "Protected check unavailable". `baseline_note` now names the candidate paths and a Spec doc missing from that change, without file text. `bounded_check_failure` keeps a reason token. `cd demo && python3 -m unittest tests.test_factory_correction_rounds` : 32 OK. `node --test demo/flue/tests/factory-checks.test.mjs` : 5 pass.

## Live status report — 2026-11-07

- `cd demo && python3 -m unittest tests.test_factory_live_status`: 5 OK. The report prints phase names and the supervisor CI lines. A reviewer sentence in the fixture stays out of the output.

## Main carries the resilience fixes — 2026-11-07

- Pull request 34 merged as a853f1a18cc4326c735eb2da28a56e0708aacfb6. develop and main match that SHA. The reviewed head a03300e has an independent Review OK. Architecture refresh run 42407731597 and CI run 42407731559 succeeded. VERSION stays 1.9.0. No tag was published.
- Controller PID 97378 stopped after an identity check. PID 29673 started in live mode. Admission exited 0 and ready() is true. The restart script exited 1 on a case-sensitive ready comparison after printing ready=True. A later read showed PID 29673 alive, mode live, listening on 127.0.0.1:8088, ready() true, and the protocol files older than the process. Build fc6f2d0d26ce was dispatched with the review retry claimed and the lease active. While the old process was stopped, one abandoned 50 USD reservation and one cancelled 5 USD reservation settled at 0. The forum purse then read settled 3.19 USD, reserved 6.00 USD, spent 9.19 USD. The incomplete forward and the review reservation stayed open. Feature 001 was not relaunched by hand. Product pull requests 7 and 8 were not merged. The publish token still cannot read branch protection.

## A resumed correction keeps the failed check — 2026-11-07

- A correction round that resumes after a network stop still carries the failed check name, the fixed repair sentence, and the reviewer line. After three resumes the next attempt still carries that check name. The two tests failed before the prompt and the crash receipt kept those lines, then passed.
- `python3 -m unittest` of correction rounds, preparation, and publication state: 61 OK. dispatch.py is 1494 lines.

## Resume reuses the prepared contract — 2026-11-07

- A same-model resume with a preparer reuses the prepared contract and does not call prepare. A refused contract is prepared again. A resumed correction round pins the interrupted model. A down provider holds network_unavailable before preparation. A linked or altered prepared folder is refused. Features 002 and 014 are prepared again.
- The three new dispatch tests failed when those branches were inverted, then passed after they were restored. `python3 -m unittest` of github atomic, budget, target dispatch, correction rounds, publication state, review reassessment, preparation and connectivity: 124 OK. knowledge-check PASS. `doc-links --diff origin/develop --worktree` PASS (152). repo-health PASS. dispatch.py is 1494 lines. store.py is 1478 lines. factory-flue.md is 522 lines.
- Feature 001 stays held. It was not relaunched. Product pull requests 7 and 8 were not merged. The publish token still cannot read branch protection. VERSION stays 1.9.0.

## Review retry, workspace replace, system CA and settled spend — 2026-11-07

- A passed gate with a reviewer failure and no earlier retry is eligible once. A refused retry is not fetched again. A same-build retry removes only that build's repo and prepared folder, refuses a symlink, and leaves another build's repo in place. A claim that never starts the author settles its reservation at zero. An author that forwarded without complete usage keeps the reservation. The summary reports settled and reserved apart from the admission total. GitHub TLS uses `/private/etc/ssl/cert.pem` when certifi cannot be imported. The cockpit shows settled spend, not the remaining purse, as the burned amount.
- Checks: `python3 -m unittest demo.tests.test_factory_github_atomic demo.tests.test_factory_budget demo.tests.test_factory_target_dispatch demo.tests.test_factory_correction_rounds demo.tests.test_factory_publication_state demo.tests.test_factory_review_reassessment` — 100 OK. `node --test demo/tests/test_cockpit_client.mjs` — 29 pass. knowledge-check PASS. `doc-links --diff origin/develop --worktree` PASS (152). repo-health PASS. dispatch.py is 1499 lines. store.py is 1478 lines.
- Feature 001 stays held. It was not relaunched. Product pull requests 7 and 8 were not merged. The publish token still cannot read branch protection.

## Review hold and the budget figure — 2026-11-07

- Build fc6f2d0d26ce finished its author, passed the gate, and held owner_review_required. qwen-3.8-flash approved. deepseek-4.1-flash returned no verdict (AGENT_TIMEOUT). Nothing was published. The measured author cost settled at about 0.09 USD.
- The forum purse for 2026-11-07 settled 3.19 USD across eight rows. Four open reservations still sum to 61.00 USD and are counted inside spent, so the summary reads spent 64.19 and remaining 85.81 of 150.00. Observability spent 0.00. The large figure is reserved capacity, not settled provider spend. The automatic review retry, workspace replace, system CA fallback, and settled-versus-reserved display are not in the code yet.

## The same correction was queued after the old workspace blocked the clone — 2026-11-07

- After preparation, build fc6f2d0d26ce held as base_unavailable. materialize refuses an existing destination. This build's prepared folder and repo were removed. The previous build's repo was kept. The same build was queued, then dispatched, and an aeion-check container was running. Features 002, 003 and 013 stayed catalog_changed.

## Admission activated and the same correction is preparing — 2026-11-07

- Native admission with controller PID 97378 exited 0: status qualified, activated true, product delivery not claimed, ready() true. The listener stayed PID 97378 on 127.0.0.1:8088.
- The queued correction was claimed and held as preparation_unavailable. The receipt error class was FileExistsError. The existing preparation folder for build fc6f2d0d26ce was removed, and that same build was queued again. A read-only query then showed it dispatched, phase preparing, with one aeion-check container. Features 002, 003 and 013 stayed catalog_changed. Pull request 8 was not merged.

## The blind correction was queued once — 2026-11-07

- The factory publish token read branch protection as HTTP 403, message class "Resource not accessible by personal access token". The default TLS context of the controller Python also fails closed; `/etc/ssl/cert.pem` verifies. The local gh session read protection as qualified (strict, enforce admins, no force-push, no deletion, five required checks) and the check runs for the open pull request.
- The only failed required check was "Knowledge, links and repository health" with conclusion failure. `repair_blind_ci` queued build fc6f2d0d26ce once. A read-only query then showed feature 001 queued, hold empty, ci_repair_retried true. Features 002, 003 and 013 stayed catalog_changed. Listener PID 97378. Admission for that process was started and is not finished. The pull request was not merged.

## CI correction controller restarted; the name reread failed closed — 2026-11-07

- Controller PID 79581 was stopped after the CI-name code was on disk. The restart script started PID 97378 and printed repair_status=unreadable. The follow-up call failed with SSLCertVerificationError before protection() returned. The receipt still stores the check name as check. Build fc6f2d0d26ce stayed held. Admission for the new protocol hash has not run.
- The earlier unit checks remain: 52 OK, cockpit client 28 pass, knowledge-check PASS, doc-links PASS (151), repo-health PASS.

## CI correction names the check and repairs a blind round — 2026-11-07

- A comma in a required check name is kept. A known check adds one fixed supervisor repair sentence. The CI log is not copied. `repair_blind_ci` replaces a placeholder name `check` and queues that same unchanged correction once.
- Checks: `python3 -m unittest demo.tests.test_factory_github_atomic demo.tests.test_factory_correction_rounds demo.tests.test_factory_publication_state` — 52 OK. `node --test demo/tests/test_cockpit_client.mjs` — 28 pass. knowledge-check PASS. doc-links PASS (151). repo-health PASS.
- Build fc6f2d0d26ce was held `correction_unchanged` when these unit checks finished. The restart result is in the section above.

## Owner reported a feature 001 launch — 2026-11-07

- After the French go message, the owner launched feature 001. A read-only sqlite query showed build 4a5e891089e0 dispatched, phase model.step.started, empty hold, empty failure token, updated age 0 seconds. Recent event names were progress. Active rows: 001 dispatched; 002, 003 and 013 held for catalog_changed. Listener PID 79581. Two OpenShell containers were up.

## Budget ceilings raised and the security proof refreshes itself — 2026-11-07

- Owner ceilings are 150 USD per repository per day and 50 USD per author execution. Review votes stay at 1 USD. `demo/budget.conf` matches those ceilings. `.env.example` carries `AEION_DAILY_LIMIT_USD=150` and `AEION_AUTHOR_MAX_USD=50`. The private env was not edited.
- A proof with an hour or more left does not start a probe. A failed probe keeps the previous file. An expired or missing file stays closed. `qualify.py` no longer removes the proof before the probe.
- A stale proof holds the same build as `sandbox_qualification_stale` and starts no author. When the check returns fresh, that same build is queued again.
- Checks: `python3 -m unittest demo.tests.test_openshell_security_window demo.tests.test_factory_budget demo.tests.test_factory_keys demo.tests.test_factory_execution demo.tests.test_factory_api demo.tests.test_factory_correction_rounds` — 97 OK. `node --test demo/tests/test_cockpit_client.mjs` — 28 pass. knowledge-check PASS. `doc-links --diff origin/develop --worktree` PASS (151). repo-health PASS.
- Feature 001 had no dispatched build. Its latest row was cancelled. Controller PID 70041 was replaced by PID 79581, listening on 127.0.0.1:8088, mode live. The security proof had 22.8 hours left, so startup did not probe. Native admission with that controller environment exited 0: status qualified, activated true, product delivery not claimed, ready() true. Feature 001 was not launched.

## Budget raise and automatic security refresh are requested — 2026-11-07

- The owner asked for 150 USD per day and 50 USD per author execution, for those two defaults in the env example, and for the controller to refresh the OpenShell security proof itself when less than one hour remains. None of that is in the tree. demo/budget.conf is still 15 / 5 / 1. The controller initial environment does not set the three AEION budget keys (listener PID 70041, booleans only). The owner fills the private env. Feature 001 was reported on hold for the daily budget and was not relaunched from here.

## OpenShell security evidence had expired — 2026-11-07

- Feature 001 build e74d624e1dc2 failed before any model request. The author failure is SANDBOX_NOT_QUALIFIED. The security evidence was 0.4 hours past its 24-hour limit. The factory tool proof was still valid. `demo/openshell/qualify.py` was run with the live controller settings and exited 0. The new evidence has 24 hours left. The owner relaunches 001.

## Qualification activated again — 2026-11-07

- Native admission with the live controller environment finished activated, product delivery not claimed. ready() is true. Controller PID 70041 listens on 127.0.0.1:8088, mode live. sandbox.blocked is absent. No OpenShell container remained before the marker was cleared.
- The first admission of the day failed preparation with SANDBOX_STOP_FAILED and wrote sandbox.blocked. The idle sweep was removing every OpenShell pair at once, including a qualification sandbox. The sweep now keeps a pair younger than 30 minutes (test_factory_connectivity). knowledge-check and doc-links --diff origin/develop --worktree passed after that change.

## Cockpit paused on a stale tool qualification — 2026-11-07

- The owner cannot select a feature. The cockpit reason is flue_factory_unqualified: Flue/Pi worker or checker qualification is missing, expired or changed. Feature 001 is cancelled. Features 002 and 003 stay on hold for catalog_changed.
- The stored proof hash 6efc295936ee2a26ccc6e751a43cfbfb6c7f9ecdb9ea4fd93cb9f94b01b4a8df predates the uncommitted protocol edits in flue_builder.py, store.py, review_circuit.py, artifact.py and dispatch.py. Admission has not been rerun. PID 66553 already loads those files.
- Idle OpenShell pairs: a live sweep removed the leftover pair. After the following restart, the listener was PID 66553 on 127.0.0.1:8088 and no OpenShell sandbox remained. The reaper is loaded by file path.

## A working CLI stop resumes the same model — 2026-11-07

- A `CLI_FAILED` with 44 tool steps, 45 forwards, finish `toolUse` and error class `IllegalStateException` queues the same build again for `deepseek-4.1-flash` and keeps the scoped file. It does not admit attempt 2. Two steps, `CLI_STARTUP_FAILED`, and `PROVIDER_ERROR` still start another model. A `TRANSPORT_ERROR` with no steps resumes the same model. The fourth working stop after three resumes is a crash. A failed provider probe holds `network_unavailable` and does not call the author. An expired lease with three `tool.finished` events is queued; one that reached `publishing` stays `reconciliation_needed`. A reviewer `TRANSPORT_ERROR` retries the same model three times.
- Checks: `python3 -m unittest demo.tests.test_factory_connectivity demo.tests.test_factory_correction_rounds demo.tests.test_factory_review_circuit demo.tests.test_factory_s2 demo.tests.test_factory_recovery demo.tests.test_factory_store` — 87 OK. `node --test demo/tests/test_cockpit_client.mjs` — 28 OK. `tools/knowledge/knowledge-check` PASS. `tools/knowledge/doc-links` PASS. The live controller was not restarted. Feature 001 was not cancelled. Nothing was committed or pushed.

## First correction author crashed; the next round is running — 2026-11-07

- Build 336259feef1e failed. Execution role author, failure CLI_FAILED, error class IllegalStateException, process exit 1, finish toolUse, 44 CLI steps, model opencode-go/deepseek-v4.1-flash. No check verdict was stored. The factory queued the next correction instead of holding the feature.
- Successor 81e212a782db is dispatched under controller PID 55334. Product pull request 7 stays unmerged.

## CI failure queued a live correction — 2026-11-07

- Native admission activated. ready() is true. Protocol evidence is demo/.local/factory/admission-h2jh_d2o/proof.json. It claims tools, not product delivery.
- Build 3044b0f5 moved from held to failed. Its correction marker is ci_failed, attempt 2, round 0. Successor 336259feef1e was admitted with idempotency factory-correction and is dispatched. A protected check process is running under controller PID 55334. Product pull request 7 is still unmerged. No tick failure was recorded.

## Controller restarted; qualification is in progress — 2026-11-07

- PID 54005 was stopped and replaced by PID 55334. The new process listens on 127.0.0.1:8088, command demo/app/server.py, mode live. No secret was printed.
- Feature 001 build 3044b0f5 stayed held. ready() was false because the stored protocol hash does not match the current tree. The held row still matches the current catalog and contract. No other 001 build is in progress, and no completed 001 row matches this contract.
- A first admission run from the shell failed at flue_openshell with ModuleNotFoundError and did not write a proof. The rerun uses the live controller environment. flue_openshell and external_acceptance passed. The proof is not activated yet.

## Controller restart is the next live step — 2026-11-07

- The owner asked to restart the controller and monitor feature 001. The restart has not run. PID 54005 still listens on 127.0.0.1:8088 with the previous code. A dry-run matched that process: mode live, no secret printed. Build 3044b0f5 is still held, publication_blocked, publisher reason ci_failed, product pull request 7. It was not cancelled.

## main and develop meet at 935744d — 2026-11-07

- Required linear history on main was disabled. Required checks `docker-demo` and `offline-examples`, admin enforcement, conversation resolution and the force-push ban stayed.
- Pull request 33 merged as `935744d955a4b52a76505ab3d1249d135ec0f643`. develop fast-forwarded to that commit and was pushed. `origin/main...origin/develop` is 0 and 0. No force-push. No version tag. The live controller was not restarted.

## Develop is pushed; main stays on a linear history — 2026-11-06

- Independent re-review of `6f7ab991b09787b37395371d5d8be486eb7ba138`: OK. The decoy path and the premature finished-rounds sentence are fixed. Receipt: `.aeion/reviews/6f7ab991b09787b37395371d5d8be486eb7ba138.md`, also posted on the commit.
- `git push origin develop` fast-forwarded `b784ccc..6f7ab99`. CI run 42307821720 and pull-request run 42308030352: `docker-demo`, `offline-examples`, and knowledge/links/repo-health passed.
- Pull request 33 (`develop` → `main`) is open. Merge commits are refused because main requires a linear history. Rebase is refused because develop contains merge `44a59a6`. No force-push. No branch-protection change. No version tag. The live controller was not restarted.

## Independent review of 4146147 was not ok — 2026-11-06

- Review of `origin/develop..HEAD` at `4146147b5f52d2b78e42d8a1fdb9cc054d255a24`: NOT OK. A Grok `read_file`, `grep`, or `list_dir` payload could name the opened path and a different decoy; the guard checked the decoy. The cockpit publication detail said correction rounds were finished for every `ci_failed` receipt, including one that had just queued another round.
- Change: disagreement between those path fields is a refusal, and the finished-rounds sentence appears only when `correction.exhausted` is true.
- Checks: `python3 -m unittest tools.agents.tests.test_hooks` — 65 OK. `python3 .claude/hooks/test_hooks.py` — 737 passed. `node --test demo/tests/test_cockpit_client.mjs` — 28 OK. knowledge-check PASS. `doc-links --diff origin/develop --worktree` PASS (150). The claude-security plugin was not run. The factory publication tests were not re-run; those files did not change in this fix.

## Develop push still waiting on an independent review — 2026-11-06

- The CI-correction commit 4146147b5f52d2b78e42d8a1fdb9cc054d255a24 is local. `git push origin develop` was refused: no `Review: OK` in `.aeion/reviews/4146147b5f52d2b78e42d8a1fdb9cc054d255a24.md`. The owner asked to advance that review. No independent reviewer ran, and no receipt was written, because the Factory 250k closure stopped the session first. origin/develop and origin/main were not moved. The live controller was not restarted.

## Required CI failure queues a correction — 2026-11-06

- Trigger: feature 001 build 3044b0f5, attempt b42253e4, PR 7. Gate passed, GLM and Qwen approved, then a required CI check failed. Publication held `ci_failed` and the feature stayed in progress, so the catalog could not continue. The forge result carried no check name. Owner-only agent notes stayed out of the next OpenShell prompt.
- Change: a completed required check that is not success closes the attempt as failed and admits the next correction in the same transaction, with at most eight check names and conclusions and a short redacted copy of the agent notes. The open pull request is not merged. Pending, unreadable and every other publication hold stay held. The last round stays held for the owner.
- Checks: `python3 -m unittest demo.tests.test_factory_publication_state demo.tests.test_factory_github_atomic demo.tests.test_factory_correction_rounds` — 42 OK. `node --test demo/tests/test_cockpit_client.mjs` — 28 OK. The live controller was not restarted and did not spend a new author session.

## Æion Factory v2.1.1 — 2026-11-06

- `tools/agents/template-update --ref v2.1.1` from the Factory checkout (885c37d089c4), baseline v2.1.0 from `.aeion-factory`. Connectors replaced for the Grok adapter: `tools/agents/hook.py`, `tools/agents/run`, `tools/context/budget.py`, `.claude/hooks/guard-path.py`, `tools/agents/connectors.py`, new `.grok/hooks/factory.json`. Hook and budget tests merged or updated. `command.md` and `Workflow_Agent.md` stay absent.
- `AGENTS.md` and `README.md` keep the project's text. The version pin is v2.1.1 and the map names `.grok/`. The factory three-way proposals conflicted with the rewritten files and were not applied. Knowledge docs state the Grok harness: hooks in `.grok/hooks/factory.json`, context size `signals.json` `contextTokensUsed`, compaction that cannot be refused.
- `.claude/hooks/guard-bash.py` stays the project copy. Factory v2.1.1 did not change it, and it still has the remote-helper URL and `--upload-pack`/`--receive-pack`/`--exec`/`-u` block the hook tests require. `adapter-check --ref v2.1.1`: 28 connectors match, this one reports DRIFT. Application `VERSION` stays 1.9.0.
- Checks: hook tests 733 passed, adapter tests 65 passed, budget tests 40 passed, `tools/factory-tests` PASS, knowledge-check PASS, doc-links PASS (150), repo-health PASS. No live Grok session was run.

## Robust author attempts, agent feedback and retention — 2026-11-06

- Trigger: build 96f9ddef (001, GLM author) stopped CLI_FAILED at step 96 (agent process exit 1, no recorded cause, 0.51 USD) and ended the launch.
- Change: one launch now makes up to three author attempts on different models, each up to two correction rounds by its own model; retryable author stops continue on a new model with the revalidated candidate, the crash code and one stderr error-class token (never stderr text). Every agent gets the same pipeline context and leaves owner-only feedback ("RAS" or ≤800 characters) in the receipt. Terminal workspaces older than seven days and the branches of failed builds whose PR was closed unmerged are removed.
- Checks: demo 788 OK (test_factory_correction_rounds 15, new test_factory_retention 7, cockpit client 28), Flue npm test 28 OK (new feedback-context), repository tests OK, knowledge-check PASS, doc-links PASS (148), repo-health PASS.
- Real Flue/OpenShell qualification (`demo/tests/qualify_factory_flue.py`): exit 0; author 7 scripted calls including `submit_feedback`, receipt feedback `{"author": "RAS"}`; 4 review and 2 Haiku calls. The log also shows span-export read timeouts to the local collector (127.0.0.1:4318), which did not affect the result.

## Go allowance multiples and appended-turn bound — 2026-11-06

- Build df71b061 (001, Claude Haiku 5.5 author): first protected self-check failed `explicit_database_less_startup_rejected` at 9 min, then BUDGET_STOP at 11 min with provider-reported 1.07936522 USD against the 2 USD cap (list-price estimate 0.40). No correction round: a budget stop is neither a rejection nor a failed gate.
- OpenCode Go page (read 2026-11-06): Haiku 5.5 lists 0.10/0.50 USD per 1M input/output up to 100K tokens and 0.50/2.50 above; the profile keeps the upper tier. The price was not the cause.
- Probe (one ~3k-token request per model, numbers only): Go reports `cost` 0 (plan), `list_cost` and an `allowance` draw. allowance/list: GLM 1.333, DeepSeek 1.2, Qwen 2.667, Haiku 4.0, Luna 4.0; Mistral bills the balance, `cost` = `list_cost` (at the 50% discount; the profile keeps the full list price). A streamed Haiku probe confirmed `message_delta` carries input, cache-write and cache-read counts, so usage parsing was correct. The budget already counted the larger amount (allowance), so Haiku's 1.08 USD was four times its list cost.
- Cause of the early stop: the next request's projection used the whole byte bound (about eight times the real input) at list price. Fix: per-profile `budget_multiplier` (rounded up) in projections, settlement bounds and the harness estimate; an appended turn bounded by the previous reported input plus its new messages; the router skips a model whose single request exceeds half its purpose's cap (Haiku: no review, no preparation); `AUTHOR_MAX_USD` 5.00 (owner request).
- Checks: demo 773 OK (new test_factory_budget_fit, AllowanceProjectionTests), knowledge-check and doc-links PASS.
- Native requalification (protocol 2970defa…) first failed: the synthetic Haiku protocol probe reused the 0.05 USD fixture review bound, which
  Haiku's 4x projection now exceeds (relay BUDGET_STOP before transport). The probe now has its own 0.25 USD synthetic bound; rerun qualified and activated, ready() True.
- Independent review of 32995e8: GLM 5.3 Flash approve (0.038 USD), Qwen 3.8 Flash approve (0.081 USD).

## Æion Factory v2.1.0 and README — 2026-11-06

- `tools/agents/template-update --ref v2.1.0` from the Factory checkout (5f8a9798a9eb): contract files replaced (build skill, template-update tool and tests, marker); patches for `agent-compatibility.md`, `engineering.md` and `owner-preferences.md` applied; `CREDITS.md` merged by hand (ub-mode credit); the `sources.md` patch skipped (project-owned research register); efficiency bundle regenerated.
- `.claude/hooks/guard-bash.py` kept as the project version: Factory v2.1.0 lacks the project's remote-helper URL and `--upload-pack`/`--receive-pack`/`--exec`/`-u` block that `test_hooks.py` and `security.md` require. `adapter-check --ref v2.1.0`: 27 connectors match, this one reports DRIFT by design (fail closed); upstreaming it to Factory is an owner decision.
- README rewritten around three parts (framework, offline examples, local factory pilot), the pipeline and a repository map. No folders moved: protocol hashes, CI paths and doc links depend on the current layout.
- Checks: hook tests 728 passed, factory-tests PASS, template-update tests OK, repository tests OK, fixture validation PASS, knowledge-check, doc-links (146) and repo-health PASS.

## Automatic correction rounds and OpenShell v0.1.7 — 2026-11-06

- Build 80463a43 (001, DeepSeek author): gate passed, GLM approved, Qwen rejected unrequested changes (removed `/__release` and `aeion.release`, default port 8081→8080); held. Its claim of two JPA repositories was checked and is false.
- Change: a reviewer rejection or failed final gate now ends the attempt as failed and queues at most two correction rounds of the same feature (supervisor admission keyed `factory-correction:<build>`, linked in the same transaction). The correction author starts from the refused candidate only when its content digest and base match, receives at most 12 sanitized, secret-redacted feedback lines as untrusted data, and gets two new votes. An unchanged correction holds `correction_unchanged` without checks or votes; after round 2 a rejection holds for the owner. The author prompt now explains the OpenShell sandbox and forbids adapting ports, routes, Compose files or defaults to it.
- OpenShell 0.1.5 → 0.1.7: release assets checked against the GitHub digests; images pinned by digest (`docker buildx imagetools inspect`, the 0.1.5 digests reproduced the existing pins). A throwaway v0.1.7 gateway with the demo configuration started with "mTLS user authentication enabled", so the v0.1.6 authentication requirement needs no opt-in. Real `demo/openshell/setup.py` qualification PASS (uid, filesystem denied, network denied, read-only workspace, outside folder invisible, no host mounts).
- Flue/Pi: Flue 2.3.0 (latest, 2026-10-12) declares `@earendil-works/pi-ai` and `pi-agent-core` `^1.1.0`, but its runtime imports `Type` from pi-ai, which 1.4.0 re-exports and 1.5.0 (2026-11-02) removed. Pi stays at 1.4.0 until a Flue release stops importing it; Flue main has no newer commit.
- Checks: demo 769 OK, cockpit client 28 OK, repository tests 33 OK, knowledge-check, doc-links and repo-health PASS.

## Byte-bound budget stop — 2026-11-06

- Build ea3fe718 (001, Qwen 3.8 Flash author at max, 08:28–08:40) failed `builder_error` `BUDGET_STOP` after 20 forwarded requests, with provider cost 0.15493343 USD of the author's 2 USD (input 974278, output 53937 tokens).
- Cause: Qwen and Haiku have no pinned local tokenizer, so the relay admits each request on a byte bound (`2 x UTF-8 bytes + 512 x messages + 16384`, about eight times the real tokens) priced at the cache-write rate, and its settlement kept that counted input after the provider had reported the real usage. Twenty settled byte bounds plus the next request's reservation passed 2 USD. The runner's native cost check (Pi estimate 0.058 USD) was not involved.
- Fix: settlement uses the provider-reported input count for provider-usage profiles and prices reported cache reads at the cache-read rate (other input stays at the higher of input and cache-write); the larger provider cost still wins, and missing or unfinished usage still keeps the whole liability. New regression tests fail on the previous relay.
- Checks: demo 759 OK, repository tests, knowledge-check and doc-links PASS.

## GPT-6 Luna and Mistral Large 4 — 2026-11-06

- Owner request: add both at max. OpenCode docs and the public models endpoint (checked 2026-11-06): GPT-6 Luna is in Go (`gpt-6-luna`, context 1050000, upper tier 0.20/0.75/0.02/0.25 USD per 1M, efforts none..max); Mistral Large 4 is pay-as-you-go only (`mistral-large-4`, context 524288, list 1.36/4.18/0.14, 50% off for now, efforts none and high).
- Probe on the paid endpoints (metadata only): Luna accepted `reasoning_effort` max, xhigh and high on Go chat completions (billing `go-plus`) and rejected an unknown value with the list none..max. Mistral answered "Model is unavailable" on Go; on pay-as-you-go it accepted high (billing `balance`) and rejected max and xhigh (supported: low, medium, high).
- Wired as profiles `luna` and `mistral`, catalog families `openai` and `mistral` behind the four measured models in the cold-start order, provider maps max to max and high, relay enforcement of the exact `reasoning_effort` without a thinking object, Mistral upstream on the pay-as-you-go URL. Checks: demo 762 OK, Flue 25 PASS. Real factory runs with these models are not yet measured.

## Max effort and green-finish author — 2026-11-06

- Build cca2f099 (001, GLM 5.3 Flash author, 01:25–02:15, 80 steps, 0.21265383 USD) failed the final gate: 1 of 60 tests, `DatabaseLessBootTest > livenessAnswersWithoutADatabase()` (Quarkus `InactiveBeanException`), reproduced by an isolated rerun in the factory's Docker check runner. The gate had recorded that name; no parser defect.
- Causes found: the author ran at provider-default effort (GLM got no effort parameter; every Flue agent asked Pi for `medium`); `MAX_CHECKS = 3` left it without feedback after its third failed check at 01:38; it stopped at 02:15 without retesting; about six shell commands ran into the 300 s sandbox command cap.
- Probe (paid Go endpoint, metadata only): GLM and DeepSeek accept `reasoning_effort: max`, GLM also beside its Z.ai `thinking` object (reasoning 6 tokens at `low`, 43 at `max`); Haiku and Qwen accept adaptive thinking with `output_config.effort: max`.
- Owner decision: max for every model and role, never medium; unlimited author checks; no finish on a red check; no Gradle in the sandbox shell. Implemented with relay enforcement for all four models, `low` kept only for a bounded review recovery.
- Checks: demo 757 OK, Flue 24 PASS (new factory-checks tests), repository tests, knowledge-check and doc-links PASS. Native qualification PASS (all seven capabilities), protocol 2ec97b297386efc5524921c0fe59d48bc8a9a2c5bb8393bb9ae5f147a18da159, proof demo/.local/factory/admission-ekojbbav/proof.json. Model quality at max effort is not yet measured.

## Busy provider retry and reviewer substitution — 2026-11-05

- Build ac5b5ce1 (001, GLM 5.3 Flash author, about 34 min): protected gate passed for the first time, Qwen 3.8 Flash approved, DeepSeek 4.1 Flash vote failed `PROVIDER_REJECTED` with zero tokens 3.3 s after its first request. The one-time operator `--retry-failed-review` ran DeepSeek first and failed the same way; the build is held `reviewer_failed`. The local privacy-filtered OTel log (`otel-logs` volume, metadata only) shows `aeion.http.status` 429 at both failures and no other refusing status today; DeepSeek had served 159 earlier requests, so the model id was valid. DeepSeek never finished a factory vote (fe0e69f0: TRANSPORT_ERROR).
- Defects: a 429 was folded into the generic refusal code; the status reached only Langfuse; nothing retried a busy provider; a busy reviewer held a passed build; the cockpit read "timeout or no typed verdict" and advised a full relaunch.
- Fix: bounded relay retry (2 retries, 5 s/20 s or `Retry-After` ≤ 30 s) for 408/425/429/5xx/529 before any byte; `PROVIDER_RATE_LIMITED`/`PROVIDER_UNAVAILABLE`; status and retry count in execution metadata; one substitution of a busy reviewer that produced zero output tokens, kept as `unavailable_reviewers` so publication still sees exactly two approvals; lease allows the extra vote; cockpit shows votes, status and the operator retry.
- Checks: demo 757 OK (12 skipped) in an isolated worktree; cockpit JS 28 PASS. Relay retries never re-claim a forward; refusals (400/401/402/403/404), timeouts and billed answers are never retried or substituted.

## Author window and stall protections — 2026-11-05

- Build 15398c1d (001, DeepSeek v4.1 Flash) ended AGENT_TIMEOUT at its 30-min window (process.retired 21:33:16); three draft self-tests and the final gate failed product_unit_tests_failed on `DatabaseLessBootTest > livenessAnswersWithoutADatabase()`; author cost 0.09768907 USD. Langfuse showed steady steps with 3–4.5 min silent gaps (long Gradle runs), so the window, not a hang, ended it.
- Owner approved a 3h cap: `AUTHOR_TIMEOUT_MINUTES` in budget.conf (5..180, default 30, shipped 180), lease and worker deadline follow it. Owner also approved stall visibility (cockpit clock, silence and failed-draft warnings) and the previous refusal of the same spec fed to the next author as bounded data.
- Checks: demo 751 OK (15 skipped), cockpit JS 27 PASS, knowledge-check and doc-links PASS. Native v17 PASS (all seven capabilities), protocol 2489713142f2a795e850a0b137286c32acd818997b1d50f31cfd338ed4e3b196, proof demo/.local/factory/admission-nwcpssfs/proof.json, `ready()` True; controller restarted live as PID 6021 with no active build.

## Dark mode and lab showcase — 2026-11-05

- Theme tokens moved to `demo/app/theme.css`; factory.css and style.css carry no hex colour. `/lab` rebuilt (idea, architecture SVG, 12 stack cards with live status where probed, circuit, playground, memory room). Memory helpers live in server.py: `memory.py` is protocol-hashed and an earlier edit to it revoked build 3bb1d4cd (ATTEMPT_REVOKED, 0.09355716 USD); restored, `ready()` True.
- Checks: node --check app.js/theme.js; cockpit JS 25 PASS; demo 745 OK (15 skipped); knowledge-check and doc-links PASS. Browser: lab and cockpit in dark at desktop, lab in light at 375 px (no horizontal scroll), checkpoint read-back matched the artifact, Hindsight recall returned 3 memories, no console errors. `?q=%01` returns 400. Owner visual yes pending.

## Draft self-test label — 2026-11-05

- Owner read "Check failed · explicit_database_less_startup_rejected" during 001 as a final failure. It was the agent's self-test of its draft (registered startup contract: the app must start when explicitly configured without a database). Build evidence now labels it "Agent self-test (draft)" until a gate exists. Cockpit JS 25 PASS.

## Controller child-process crashes — 2026-11-05

- Owner report: hundreds of macOS "Python quit unexpectedly" dialogs. Crash reports (4 kept by macOS, 20:01–20:10) are children of controller PID 77547 aborting 6 ms after launch with EXC_BREAKPOINT in libxpc, called from gRPC's c-ares DNS resolver on a gRPC work-stealing thread.
- Cause measured: with a live gRPC channel, a forked child has 10 native threads by default (gRPC restarts its pool after fork) and 1 with `GRPC_ENABLE_FORK_SUPPORT=false`. A child aborting before exec fails that subprocess launch, a plausible cause of the transient `isolation_unqualified` draft check in 001 (its detail code is not retained, so unconfirmed).
- Fix: `demo/app/grpc_fork.py` forces the variable before the OpenShell import in the controller and `openshell/qualify.py`. test_grpc_fork 3 PASS (fork probe asserts one child thread). It applies after the next controller restart, which waits for the running 001 build to finish.

## Simplified cockpit — 2026-11-05

- Owner request: the cockpit and lab pages were unclear, with no visible staging or production link. Change: a "Your next step" banner with one plain action, then factory mode, today's budget and environments (Staging/Production "Not deployed yet"). The synthetic canary drill is removed from the cockpit; review holds read `reviewer_failed`/`reviewer_rejected` from the circuit; the lab page says it is advanced and not needed to build.
- Checks: cockpit JS 24 PASS (2 new: next-step actions, no drill or fake environment link); full demo suite OK; knowledge-check and doc-links PASS.
- Rendered with a synthetic fixture backend (scratchpad, no auth, no real data) at the pane's desktop width and at 375 px: banner, three status blocks, catalog and held build card readable. Owner visual yes on the real signed-in cockpit is still pending. Dark mode is not implemented in these stylesheets (existing gap).

## Typed review verdict and relay idle bound — 2026-11-05

- Measured: DeepSeek review run44bef4bd ended with one known-cost request and no `submit_review` call (REVIEW_RESULT_MISSING). Fix: Flue2.3 `useAgentFinish` appends one result-required signal guarded by `usePersistentState`; the packet system text now points to the typed tool. Native fixture `qualify_review_verdict.py` failed before the hook (REVIEW_RESULT_MISSING) and passes after it (3 scripted requests, one continuation, zero provider requests).
- Failed circuit votes now keep trusted execution metadata and the failure code. `--retry-failed-review` allows one operator retry after a v2 hold with only approve/error votes; tests cover replacement of both votes, no author rerun, a second failure staying held and unknown reservations staying counted.
- Native v14 qualification PASS, protocol28b65bec, proof `demo/.local/factory/admission-sosnp6_4/proof.json`; controller reloaded as PID66026 with health/live/sandbox ready.
- Actual 001 retry (generation2): external gate PASS, then DeepSeek failed `TRANSPORT_ERROR` with zero tokens. Langfuse trace d52dbac0 shows preflight 18:11:52.779Z and provider.failed 18:12:38.157Z: 45.4s, the relay's fixed 45s socket bound. The previous DeepSeek review request lasted 174s. The one-time retry is consumed; the build stays held and no product publication occurred.
- Fix: relay upstream idle bound 300s (`UPSTREAM_IDLE_SECONDS`), stalls classified `PROVIDER_TIMEOUT`. New relay test fails without the change and passes with it. Full demo suite735PASS75.9s; Flue npm test PASS; root tests33PASS; fixtures PASS; knowledge0problems; doc-links144PASS; repo-health PASS.
- Native v15 qualification after the relay fix PASS, protocol5c03f914, proof `demo/.local/factory/admission-8cwj4ey3/proof.json`; controller reloaded as PID70968, health/live/sandbox ready, no active build.
- Owner decision 2026-11-05: up to $15/day and $5 per author execution in the extreme case, configurable, with safeguards. `demo/budget.conf` (DAILY_LIMIT_USD15, AUTHOR_MAX_USD2 default, REVIEW_MAX_USD1) is validated against code ceilings 15/5/1 plus author+2 votes within the day; an invalid file holds `budget_config_invalid` and zeroes the purses. 7 new tests; full demo742PASS79.7s, cockpit22PASS, Flue19PASS, root33PASS, knowledge/doc-links144/repo-health PASS.

## Frozen-base review context — 2026-11-05

- Actual product001v8 reached a full passing external gate, then Qwen rejected inherited SQLite/Expo/endpoint code as new scope. Inspection confirmed its packet included current files but no base diff. No vote override or product merge occurred.
- New envelope includes the exact frozen Git diff, complete changed files, MD and protected acceptance; regular/size/secret bounds refuse unsafe baseline reads. Coverage binds base/diff hashes even on rejection.
- A single explicit operator-only old-envelope reassessment archives the original receipt and increments the generation. Changed contracts/base/artifact, unknown usage, cancellation, prior publication and a second v2 rejection cannot resume. It reuses the actual author's execution/cost, reruns the final gate and obtains two fresh votes including the original rejecting model. No business source was hand-edited.
- Regression commands: controller venv full demo suite730PASS82.503s (`/private/tmp/aeion-review-context-full-v2.log`); cockpit Node22PASS; knowledge0problems; doc-links142PASS; repo-healthPASS. The first sandboxed full run failed on77denied loopback sockets; the same authorized socket-enabled command passed. The new baseline tests initially failed because the missing function did not exist; state/dispatch tests prove fencing, preserved rejection, exact artifact, fresh gates/votes and review-only cost.
- Nativev13 qualification is running and is not yet claimed passing. No final operational Go or staging/production delivery is implied. The old advanced canary panel is now explicitly labelled a historical synthetic drill.

# Research validation — 2026-10-23

Scope: local research artifacts only. This is not provider, security-boundary, backend or
controller qualification. All 32 runtime qualification cases remain planned.

## Checks performed

| Check | Result | Scope |
| --- | --- | --- |
| Factory `knowledge-check --root` | PASS | Frontmatter, component sections, document limits and knowledge links |
| Factory `doc-links --root` | PASS | Declared source/spec links; no application code exists here |
| Whole-folder Markdown target check | PASS | Relative file targets, including root/example docs |
| HTTPS reference-link HEAD checks | 87/87 returned final HTTP 2xx | Link reachability, not semantic correctness or permanent availability |
| Strict JSON/JSONL parsing | PASS | Valid syntax, no duplicate object keys/non-finite constants in fixtures |
| Retrieved source fingerprints | 66/66 matched temporary fetched bytes | SHA-256 identity only; source reading depth documented separately |
| Policy fixture | PASS | Shadow mode, application/learning disabled, no live-qualified arm, both authentication modes represented |
| Session fixture | PASS | 13 delivered events, 12 unique; one intentional duplicate, two distinct charges |
| Retry/duplicate arithmetic | PASS | `0.02 + 0.03 = 0.05 USD`, not one charge or a duplicated total |
| Artifact/task/check consistency | PASS | Matching fictional IDs, digests and check references |
| Cohort calculation from README | PASS | Same ten synthetic task identities per policy; totals and nearest-rank p95 recomputed |
| Text/size hygiene | PASS | Balanced fenced blocks, no NUL/CR, files below 1 MiB |
| Selected common credential patterns | No match | Limited sanity check; not an exhaustive secrets/security audit |

Commands run from the parent workspace:

```sh
Æion_Factory/tools/knowledge/knowledge-check --root "$PWD/Æion_Observability"
Æion_Factory/tools/knowledge/doc-links --root "$PWD/Æion_Observability"
```

Additional checks used inline standard-library Python and read-only HTTPS HEAD requests. The
worked arithmetic is reproducible with the command in `examples/README.md`. Temporary retrieval
and link-check logs live under `/private/tmp/aeion-observability-research-20261023`; they are not
permanent vendored upstream content.

## Recomputed synthetic arithmetic

| Policy | Cohort cost | Inference cost/request | Autonomous successes | Cost/autonomous success | p95 wall time |
| --- | --- | --- | --- | --- | --- |
| Cheap | $72.00 | $0.05 | 6/10 | $12.00 | 1,800 s |
| Balanced | $82.00 | $0.15 | 9/10 | $9.111… | 600 s |

These figures validate arithmetic only. They are not model benchmarks, measured savings,
statistical promotion evidence or a recommendation to deploy either fictional profile.

No real transcripts/credentials were inspected, no telemetry plugin installed, no backend
deployed, no paid inference request made, and no remote repository published by this work.

## Offline safeguard implementation — 2026-10-25

Scope: approved state-of-the-art plan v1/P1 and P2, validated locally on macOS/Python 3.12.8.
No runtime qualification scenario, provider call or backend deployment was performed.

| Check | Result |
| --- | --- |
| `python3 examples/compare_cohorts.py` | Original USD 72/82, 6/9 successes and p95 1800/600 unchanged |
| `python3 examples/validate_fixtures.py` | PASS: 5 JSON files, 13 deliveries, 12 unique events, 2 charges, USD 0.05 |
| `python3 -m unittest discover -s tests -v` | 33 tests passed |
| Factory knowledge and doc-links gates | PASS; includes documentation coverage for changed files |
| YAML, relative Markdown links and whitespace | PASS; CI triggers/permissions and original data fixtures unchanged |
| Python 3.9 grammar parse | PASS; not a runtime test on Python 3.9 |

The regressions cover mismatched/reordered cohorts, absent quality fields, duplicate JSON keys,
non-finite numeric results, synthetic observe/shadow guards, cross-file evidence links,
event claims that contradict shadow controls, identical/conflicting redelivery and charge
completeness/arithmetic. The new CI step runs the
same offline validator. These checks do not establish production privacy, durability, billing,
provider compatibility or autonomous task success. Hosted CI has not run for this local change.

## Authorized Docker agent atelier — 2026-10-25

This subsequent owner-approved pilot adds real local backends and bounded paid Go inference.
The research-only statements above describe earlier work, not this pilot. Implementation is
on `task/langfuse-opencode-demo`. Subsequent PR/main publication was authorized in chat;
these local checks do not establish a hosted CI outcome or production deployment.

| Check | Verified result |
| --- | --- |
| Existing offline tests and fixture CLIs | 33 tests pass; original cohort arithmetic and 5-file fixture accounting unchanged |
| Demo Python checks in its built Docker image | 14/14 pass, including both official tokenizer templates, exact 300k reservation boundary and concurrent refusal during a held checkpoint |
| Node hook/gate checks | 7/7 pass, including cache accounting, missing/stale Markdown acknowledgement, single build admission ticket and 4,096 output cap |
| Real OpenCode 1.19.4 CLI, local fake inference only | PASS: four local requests, two distinct sessions, partial artifact preserved, durable MD loaded into successor prompt, MD-before-close ordering, retired runtimes removed and 12/12 Deno checks |
| Docker stack | All eleven services running; configured health checks pass and all five cockpit integration probes return connected |
| Deno/Hono target API | Correct EUR 3.25 quote; malformed/invalid inputs return 400, >4 KB body returns 413 |
| Real Go tasks | GLM 5.3 Flash and DeepSeek V4.1 Flash each pass the protected 12-check task under method `go-build-v2-counted` |
| Langfuse backend reads | Actual generation observations, native cost estimates, empty input/output fields, matching boolean scores and joined Deno HTTP service span verified |
| Memories | claude-mem save/readback and Hindsight retain/semantic recall verified; retain reports zero LLM tokens |
| Human-assistance correction | Replay attestation is idempotent, preserves correctness, removes autonomous success and updates the same Langfuse score IDs and Hindsight document |
| Logs | Sequenced fsynced local audit and Collector OTLP log readback; canonical bodies, trace/span/run identity, gate/MD/retirement and intervention events verified |
| UI | Actual browser checks: sober AEion illustration/palette, connected services, replay, 250k gauge, MD/log links, real/synthetic filters, model map, memory recall and Deno quote interaction |
| Documentation / whitespace | Factory knowledge and doc-links gates plus `git diff --check` pass |

Comparable native Go estimates (not invoices or subscription-credit reconciliation):

| Model | Run | Generations | Protected checks | Native estimate USD | Task elapsed |
| --- | --- | --- | --- | --- | --- |
| DeepSeek V4.1 Flash | `4555981949004d1c843ba4b22e26f4b5` | 3 | 12/12 | 0.000994308 | 23.9 s |
| GLM 5.3 Flash | `361bd3bc40cb4ad1a9fa4662b8c0d42e` | 5 | 12/12 | 0.00284815 | 35.7 s |

One observation per comparable profile on one tiny task cannot establish a general model
winner. Earlier protocol-qualification success/failure remain visible as an unversioned
cohort; the initial provider rejection retains unresolved usage instead of a zero-cost claim.

The 250k transition is tested without buying a 250k-token inference. The credential-owning
relay counts the full request independently, reserves output plus 20k framing and refuses
unknown/over-budget proposals before upstream dispatch. Waiting for the MD cannot admit a
further provider call. Tokenizer/template parity and framing remain explicit provider
qualification assumptions; no guarantee about undisclosed provider internals is inferred.
Native >300k or >20k count drift disables live admission pending requalification. Backend
outages do not remove the local audit; complete crash-proof/exactly-once export, hostile-code
isolation, general task quality and billing reconciliation are not qualified here.

Approximate idle memory observed with Docker stats: supervisor 111 MiB, Hindsight 849 MiB,
Langfuse web 877 MiB/worker 464 MiB and ClickHouse 960 MiB. This local eleven-service stack is
intentionally heavier than the supervisor itself. Existing sibling containers were preserved.
Hosted CI runs separately through the release PR; its Docker job uses fake inference only.

## OpenShell migration and expanded model lab — 2026-10-27

The earlier two-model Docker results above are historical evidence. They are deliberately
excluded from current OpenShell selection. Current method: `openshell-go-v5` (see the
search-tool correction below).

- Official OpenShell 0.1.5 native gateway/SDK, SHA-verified releases, pinned runtime/supervisor
  image digests and immutable local agent image ID. Actual probes confirm UID 10001, denied
  system writes/outbound requests, workload network `none`, no socket and propagated NVIDIA
  telemetry=false. Security qualification expires after 24 hours.
- Real OpenCode 1.19.4 through OpenShell, local fake inference: six requests, successful
  offline `glob`/`grep`, two fresh
  sessions, MD-before-close/ack, preserved partial artifact, successor MD load, removed
  runtimes, and 12/12 checks. Separate >300k/concurrent-admission and missing/stale-ack tests pass.
- All five official tokenizer/templates count a text/tool roundtrip. Four reference contracts
  pass 12+14+14+14 protected Deno cases inside OpenShell; deliberately broken artifacts fail.
- Unit tests exercise per-task routing, cost/speed objectives, incomplete usage, failures,
  assistance, legacy/synthetic/runtime separation and gate-cohort evidence IDs.
- Startup denied runtime npm/model discovery as intended. Bundled model metadata and read-only
  plugin config remove those downloads; exact executable identity is the shipped OpenCode
  binary. No broad egress was added. A loaded shared 8 GB Docker VM caused substantial cold
  startup delays and one deletion timeout; admission stayed closed and deletion was confirmed
  before requalification. Other projects were not stopped or modified.

The latest harness commit `4efc12b` passes both hosted CI jobs
([run 40485917551](https://github.com/OualidGuennif/aeion-observability/actions/runs/40485917551)).
Local runtime checks pass 20 Python tests and seven Node gate tests; the existing offline
suite passes 33 tests. Paid campaign and full-stack receipts follow below.

Provenance: the evidence `harness_commit` values (`4efc12b`, `0039d7a…`) exist on branch
`task/openshell-safe-model-lab`, not on `main`. Squash commit `f2b9c22` (PR #4) has the same
tree as that branch tip `0bccce4`, and `demo/` is unchanged since `4efc12b` (empty `git diff`).
Keep that branch while those receipts are cited.

### Search-tool qualification correction

The first paid matrix (`openshell-go-v4`) completed 40 attempts with 31 accepted outcomes,
complete native usage and $0.398896882 in CLI estimates. All 40 analyses and the decision
snapshot were retained with zero LLM tokens. The data remains in
[evidence/2026-10-27-openshell-model-lab-v4.json](evidence/2026-10-27-openshell-model-lab-v4.json).

Review found repeated search-tool errors. A direct OpenShell probe confirmed no system
`rg`; pinned OpenCode 1.19.4 source resolves system ripgrep first and otherwise downloads it
from GitHub, which the required egress policy correctly denies. The image now preinstalls
that dependency and qualification forces successful `glob`/`grep` before the existing
read/write/handover sequence. The acceptance cases and context gates are unchanged.
Method `openshell-go-v5` separates the corrected environment; v4 is historical evidence and
is excluded from its routing. No network permission was broadened.

### Corrected paid campaign and backend readbacks

The frozen `openshell-go-v5` matrix completed **40 attempts: 36 accepted outcomes and four
`CLI_FAILED` outcomes**, with complete native usage and **$0.368068181 in CLI estimates**.
Each of the five paid Go profiles ran each of four tasks twice, sequentially with rotated
model order. No artifact was manually repaired during the campaign. Failures and their costs
remain in the cohorts; two complete autonomous successes are required per eligible task/profile.

| Task | Lowest observed cost | Shortest observed time | Equal cost/time weights |
| --- | --- | --- | --- |
| Cart totals | GLM 5.3 Flash | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Shipping rules | DeepSeek V4.1 Flash | DeepSeek V4.1 Flash | DeepSeek V4.1 Flash |
| Exact discount arithmetic | DeepSeek V4.1 Flash | DeepSeek V4.1 Flash | DeepSeek V4.1 Flash |
| Normalize and merge a cart | GLM 5.3 Flash | DeepSeek V4.1 Flash | DeepSeek V4.1 Flash |

These are observations on tiny synthetic contracts using real paid CLI calls, not general
model rankings. Two repetitions under shared-host memory pressure do not establish statistical
superiority. In particular, the pricing medians are 43.17 seconds for GLM Flash and 42.93 for
DeepSeek Flash. End-to-end time includes sandbox/CLI startup, verification and the app probe.
Native estimates are neither invoices nor a remaining Go balance; infrastructure and memory
overhead are separate. DeepSeek remains subject to the runbook's 2026-10-31 requalification date.

Independent readbacks confirm:

- All **40 Hindsight session documents** equal their canonical analyses; the campaign decision
  document equals the frozen recommendation snapshot. Every retention reports zero LLM tokens.
- All **40 durable JSONL audits** equal their reports and have contiguous event sequences.
  Each admitted runtime has a retirement event before its session is wiped.
- All **36 claude-mem checkpoints** read back with the expected task, artifact hash, agent and
  protected check result. Early CLI failures did not publish an accepted artifact/checkpoint.
- Six Langfuse receipts cover the five models and a failed attempt: generation coverage,
  native cost mapping and Boolean correctness/autonomy scores match. Content fields are empty;
  successful app probes join the Deno service to the same trace.
- OpenTelemetry, Langfuse, Hindsight, claude-mem and the Deno playground are connected.
  **Nine HTTP checks** pass across all four public scenarios, quote calculation, invalid
  arguments, unknown scenarios and oversized bodies.

Evidence: [matrix](evidence/2026-10-27-openshell-model-lab.json),
[backend receipts](evidence/2026-10-27-backend-receipts.json),
[playground HTTP checks](evidence/2026-10-27-playground-checks.json).

Hindsight uses chunk retention and RRF recall with reranking/consolidation disabled: useful
semantic recall without an extra LLM or a cross-encoder on this loaded host. Existing banks
were set to the same reranking configuration; the Compose settings preserve it for new banks.

### Auto selection, handover replay and browser checks

After freezing the matrix, an **Auto** shipping build selected DeepSeek from its two measured
campaign successes and passed 14/14 checks for $0.000901692 in native estimates. Its selection
stores those exact evidence IDs. This additional run is outside the 40-attempt matrix.

A separate, explicitly synthetic shipping replay prepared the MD before closing the 250k
gate and starting the successor, confirmed retirement of both OpenShell sandboxes, preserved
the MD hash and passed 14/14 checks. It spent no model quota. The copied
[HANDOVER.md](evidence/2026-10-27-synthetic-HANDOVER.md) is byte-identical to the prepared
replay document. The real CLI/fake-inference qualification separately exercises its nonce
acknowledgement and two fresh OpenCode sessions; the synthetic animation is not that proof.
Langfuse and Hindsight readbacks also pass for both post-campaign runs.

Actual browser checks cover four connected tool indicators, current-method/task filtering,
five profiles, cost/speed/combined objectives, a real Auto launch, replay state/MD/log links,
memory recall, all four Deno scenarios and invalid JSON feedback. The pricing selector shows
GLM for cost and DeepSeek for speed; shipping shows DeepSeek for the combined objective.
The existing ivory/forest/copper artwork and typography remain in place.

Evidence: [post-campaign receipts](evidence/2026-10-27-post-campaign-checks.json),
[250k cockpit screenshot](evidence/2026-10-27-handover-cockpit.png),
[measured model map](evidence/2026-10-27-model-lab.png). The model-map screenshot includes
the additional Auto shipping run; the frozen matrix remains the original 40 attempts.

## Repository review follow-ups — 2026-10-27

A repository review found defects outside the qualified protocol. This first batch leaves the
`protocol_hash()` inputs, the qualified bundle and the agent image inputs byte-identical to
`main`, so the existing sandbox/CLI qualification still applies. No paid model call was made.

- **Linux gateway detection:** `ps -o comm=` reports `openshell-gatew` (15 characters), so
  bootstrap never recognized its running gateway and a rerun started a second one. It now
  compares the launched executable path from `ps -o command=`; a regression test spawns a
  long-named process.
- **Restart recovery:** a controller stop during Hindsight retention left `memory.status=pending`,
  which disabled every cockpit action indefinitely. Startup now marks it `interrupted`. A
  scratch-path run of the real `server.py` with seeded stale reports confirmed the reset,
  the interrupted campaign and an `interrupted` (not `pending`) KPI count.
- **Campaign total:** one plan now drives both execution and the advertised total, so expired
  profiles are neither run nor counted. Its order matches the previous loop for all-available
  and DeepSeek-expired catalogs.
- **Playground read scope:** with `--allow-read=/work`, an accepted artifact could read another
  run's `HANDOVER.md` (reproduced with Deno 2.5.6). The scope is now `/work/published`; the
  same probe is refused, while a published solution still returns the expected result.
- Telemetry severity and the log allowlist now match the audit; the claude-mem Bun base image
  is digest-pinned (content-addressed index verified against the registry).

Checks: offline suite 33 tests; demo host suite 26 tests (4 Docker-only skips); seven Node gate
tests; fixture validator pass. Not run here: Docker image builds, the OpenShell/CLI
qualifications and the hosted CI jobs.

Remaining, protocol-hashed and therefore requiring requalification: `check-scenario.js` counts
`TypeError` cases as passed when the artifact cannot load (a syntax error reports 9/12), the hook
writes its gate file non-atomically, the cost-stop default differs between hook and supervisor,
and `runner.py` keeps dead constants.

## Protocol review follow-ups — 2026-10-27

This second batch changes `protocol_hash()` inputs, the qualified bundle and the agent image
(`context-gate.mjs`, `fixtures/`, `runner.py`). Existing local sandbox/CLI qualifications
therefore stop admitting live runs until bootstrap and CLI qualification are rerun.
Acceptance decisions are unchanged: every contract still has cases that require a returned
value, so an unloadable artifact failed before and fails now. Existing `openshell-go-v5`
cohorts remain comparable; only the reported check counts of such failures change.

- **Unloadable artifacts:** `check-scenario.js` called an undefined export, and the resulting
  `TypeError` satisfied every case expecting one (a syntax error reported 9/12). The export
  must now be a function before any case can pass. With Deno 2.5.6, syntax-error, non-function
  and missing exports report 0/12; the four reference solutions still report 12/14/14/14.
  `qualify_scenarios.py` now asserts zero passed cases for an unloadable module inside OpenShell.
- **Atomic hook state:** the hook rewrote `gate.json` in place while the supervisor polled it;
  an empty read failed the run as `RUN_FAILED` instead of a handover. All hook state files now
  use write-then-rename. A hard-link regression test fails on the previous hook and passes now.
- **One cost-stop default:** the hook budget defaulted to $0.10 and the supervisor stop to $0;
  both now use the documented $0.10. Compose already set it, so the qualified stack is unchanged.
- Removed unused `TASK`/`SOLUTION` constants, a no-op `try/except` and two unreferenced fixtures;
  the cockpit shows each task's own check total; hosted CI now runs the Docker-free demo checks.

Checks: offline suite 33 tests; demo host suite 27 tests (4 Docker-only skips); eight Node gate
tests; fixture validator pass; `runner.py` imports with the pinned requirements. Not run here:
image builds and the OpenShell/CLI qualifications (hosted CI runs both on Linux).

## Flue + Pi harness with OpenShell sandboxes — 2026-10-27

The execution layer changed; gates, scenarios, memories, telemetry and KPIs did not. Facts that
shaped it were checked against primary sources (pinned in the
[component specification](../knowledge/components/docker-demo.md#data-sources)): Flue's harness is
built on Pi, its `local()` sandbox has no isolation, its OpenTelemetry adapter exports content by
default, `flue run` persists conversations unless a database is configured, and compaction is on
by default. Daytona's open-source repository is archived ("no longer maintained", June 2026) and
no Flue sandbox adapter offers a maintained local isolation runtime, so OpenShell is reached
through a Flue adapter. Harness² is a Python research framework with unrestricted executor
network access; it is not used.

Measured on the wire with Flue 2.3.0/Pi 1.4.0 and a local fake server: Pi sends only
system/user/assistant/tool roles, `max_tokens: 4096`, `stream_options.include_usage`, its own
`User-Agent` and a stable `x-opencode-session` (the Go client requirements); a relay 409 is not
retried and fails the submission without compaction; turn usage reports `input` excluding cache
reads, so `input + cacheRead + cacheWrite` equals the provider prompt count.

A design gap surfaced and was closed. Unlike OpenCode, the coding agent now has a shell, and the
image previously held the protected expected results. Checks now receive cases on stdin, the image
no longer contains them, and the final verdict runs in a fresh sandbox without agent processes.

The first hosted run showed that OpenShell's default resource admission refuses raw host bind
mounts ("no trusted label resolver"); only operator-labeled Docker volumes are admitted, and
bind-backed ones also need `enable_bind_mounts`. The work folder is therefore one labeled
host-backed volume and each sandbox mounts only its run subpath.

- `qualify_flue.py --local-sandbox` (real Flue CLI, Pi, relay with admission barrier, bridge,
  helper and Deno 2.5.6 checks; host stand-in for OpenShell): passed with 6 forwarded requests,
  2 fresh conversations, MD before the refused request at a native 250k report, 12/12, complete
  usage, no compaction, no persisted conversation store and no prompt text in events.
- `qualify_scenarios.py --local-sandbox`: 12/14/14/14 reference cases; broken and unloadable
  artifacts fail.
- Bridge round trip through the real TypeScript adapter; observer canary test; provider
  configuration test; relay admission refusal before forwarding; host-native cockpit start.
- Offline suite 33 tests; demo suite 32 tests (pinned venv, 4 tokenizer-file skips); Flue 5 tests.
- Hosted CI on Linux ([run 40576060598](https://github.com/OualidGuennif/aeion-observability/actions/runs/40576060598),
  commit `65bf79b`, real OpenShell 0.1.5): security qualification passed with agent UID 1001,
  Landlock denial, read-only workspace, invisible host paths, network mode `none`, network denied,
  NVIDIA telemetry off and the labeled work volume; demo suite 32 tests with the pinned tokenizer
  files and no skips; `qualify_scenarios.py` 12/14/14/14 with broken and unloadable artifacts
  failing; `qualify_flue.py` passed in `openshell` mode with 6 forwarded requests, 2 fresh
  conversations, 12/12 and complete usage.

Not verified: macOS ownership of the host-backed work volume and any paid Go request, including
Go's acceptance of the forwarded Pi identity. Earlier `openshell-go-v5` evidence stays historical
and is excluded from Auto selection.

## Triage and local-assistant tiers — 2026-10-27

Tiers 1 and 2 reuse the tier 3 relay, gates, handover, observer, audit, telemetry and memories;
only the sandbox, tools and verdict differ. Checked against the pinned Flue documentation
(sandboxes, skills, tools) and the installed packages: the just-bash virtual sandbox emulates
commands in-process over an in-memory filesystem with network opt-in; Flue's `bash` tool takes
`command`, `activate_skill` takes `name`; a `defineTool` handler that throws returns the error to
the model. Observed with just-bash 3.6.0 and the `hardened` profile: `jq` works, host
`/etc/passwd` is absent and `curl` is not a command when no network is configured.

Tier 2 (`restricted-local`) restricts model-facing tools only: path confinement, symbolic links
refused on every component, `O_NOFOLLOW`, writes only under `src/`, and no shell, grep or glob.
The harness process keeps the host user's privileges; that is documented, not hidden. Tier 1's
harness receives only events and labels; the frozen answers in `demo/fixtures/triage.json`
(synthetic, eight events) are recomputed independently from the contract rules by a unit test.

- `qualify_flue.py --local-sandbox` (real Flue CLI and Pi, fake inference, host stand-in for
  OpenShell): tier 3 unchanged (6 requests, 2 fresh conversations, MD before the refused request
  at 250k, 12/12); tier 2 passed with 5 requests, no shell/grep/glob offered, the strict skill
  loaded, a `package.json` write refused back to the model with no file left, 12/12; tier 1
  passed with 5 requests, `jq length` = 8, host file invisible, an incomplete submission refused
  without writing, 8/8 and no sandbox event. Complete usage, no compaction, no persisted
  conversation store and no prompt text in events for all three. A negative control (a failing
  fake-inference assertion) failed the run with `CLI_FAILED`.
- Cockpit on the controller venv without OpenShell: the catalog lists tasks per tier, readiness
  enables triage simulation only, an off-tier task and a non-tier-3 benchmark are refused, and
  a simulated triage run passed 8/8 through a handover with no sandbox. Chromium: the tier selector
  repopulates tasks and controls with no console error. OTel export errors were expected (no collector).
- Offline suite 33 tests; demo suite 40 tests (8 skips on system Python, 4 tokenizer-file skips
  on the pinned venv); Flue 14 tests; fixture validation and cohort comparison passed.

- Hosted CI on Linux ([run 40589836618](https://github.com/OualidGuennif/aeion-observability/actions/runs/40589836618),
  commit `944d237`, real OpenShell 0.1.5): security qualification passed as for tier 3; demo suite
  40 tests with the pinned tokenizer files and no skips; Flue 14 tests; `qualify_scenarios.py`
  12/14/14/14; `qualify_flue.py` in `openshell` mode passed tier 3 (6 requests, 2 fresh
  conversations, 12/12), tier 2 (5 requests, 1 conversation, 12/12 from a fresh OpenShell
  verdict) and tier 1 (5 requests, 1 conversation, 8/8), all with complete usage.

Not verified: any paid Go request in any tier.

## Local stack end to end, and Langfuse v4 — 2026-11-01

Fresh start: `demo/.local` was regenerated (new random credentials), the old Compose volumes were
removed, the images rebuilt, and the ten services came up healthy on Docker 29.9.2
(`langfuse-web` 4.49.0, worker, Postgres 17, ClickHouse 25.12, MinIO, Redis 7, OTel collector
0.163.2, Deno playground, Hindsight 1.1.0, claude-mem). `GET /api/public/health` answers 200 and
the cockpit reports `5/5` integrations connected.

- **Supervisor spans reach Langfuse.** One synthetic triage replay (`flue-just-bash`, handover
  through the 250k gate) wrote 22 observations in `environment=default`: `demo.task`,
  `agent.started`, `gen_ai.request` ×5, `gate.closed`, `handover.prepared` ×3, `agent.handover`,
  `artifact.checked` ×2, `session.wiped` ×2, `memory.checkpoint` ×2, `memory.retained`,
  `quality.scored`, plus one playground `GET`. The run passed 8/8 checks.
- **Scores are accepted.** `POST /api/public/scores` returned both deterministic ids
  (`demo_verified_checks`, `demo_autonomous_success`) for that run.
- **claude-mem** saved and read back checkpoint `#2`; **Hindsight** retained the analysis in
  `aeion-demo-synthetic`. Both are real services, not stand-ins.
- **Pi → Langfuse, verified.** The `@langfuse/pi-observability-plugin` 0.1.2 ran from the ignored
  `.tmp/pi-agent` agent directory (`PI_CODING_AGENT_DIR`), against a local OpenAI-compatible
  fixture, never a paid provider and never `~/.pi/agent`. Three sessions produced three
  `Conversational Turn` spans and three `LLM Call` generations in `environment=development`,
  with `input=1234`, `output=56`, latency, time-to-first-token, session id and trace id, and with
  the raw prompt (58 chars) and output (35 chars) attached.
- **Langfuse v4 events_only changes the API surface.** `GET /api/public/traces`,
  `GET /api/public/sessions` and `GET /api/public/scores` answer 404 with
  *"not available on deployments running in Langfuse v4 events_only mode"*. Reads go through
  `GET /api/public/v2/observations` and `GET /api/public/v2/metrics`; score creation still works.
  Any read-back procedure that still calls the v1 resources is dead on this instance.
- **Flue harness re-qualified** with `qualify_flue.py --local-sandbox` (real Flue 2.3.0 + Pi 1.4.0,
  fake inference): tier 3 6 requests / 2 fresh conversations / 12 checks, tier 2 5 requests /
  12 checks, tier 1 5 requests / 8 checks, all complete usage.

**OpenShell on macOS is not qualified and does not run.** `openshell/setup.py` builds the agent
image and starts the gateway, then fails in `qualify.py` because the probe's `exec` returns an
empty stdout. Measured cause, not a guess: on the host-backed work volume, writes are *performed*
(the files appear on the host) while the syscall returns `EACCES` — `open(..., "w")`, `: > file`
and `echo > file` fail this way, `touch` sometimes succeeds, and repeated probes disagree with each
other. The same write succeeds in a plain container on a Docker volume-subpath mount and on the
same bind mount, `os.access(..., W_OK)` is `True`, and `/tmp`, `/sandbox` and a tmpfs mounted
inside the sandbox all accept writes normally. Host bind mounts are refused by admission
(*"host bind or image mount cannot be attached while resource admission is enabled: no trusted
label resolver"*), so the volume path is the only admitted one. The qualification therefore fails
closed, as designed, and tier 3 stays unavailable locally.

Not verified: any paid Go request; tier 3 in a real OpenShell sandbox on this machine.

## Factory v1.8.3 import completed — 2026-11-01

The template import was missing the `loops/` payload its own tools already named, so
`tools/factory-tests` stopped at `tools/loops/tests/test_loops.py` with
`FileNotFoundError: .../loops`. Fixed by importing `loops/` from the sibling Factory checkout at
tag `v1.8.3` (15 files: `orchestrator.sh`, six job prompts, schedules, model routing, issue
protocol, Decisions API client), without `.DS_Store` and without editing the sibling.

- **`env.local` is now ignored**, as in Factory: the orchestrator reads loop settings from it and
  the file may also carry the Decisions API secret. Only the template is tracked.
- **doc-links rule L4 caught the new spec headers**: `loops/orchestrator.sh` and
  `loops/decisions-api/client.sh` name `knowledge/operations/loops.md` as their spec, so that
  runbook now lists them as `sources:`.
- **`repo-health` counts nine top-level folders**, the cap, once `loops/` is tracked. The imported
  `skills/` pool would have made ten: it is generated and verified by its own integrity check, so
  the scorecard now counts it with the sources instead of the hand-made folders (one line plus a
  comment, and the policy sentence in `knowledge/policies/engineering.md`). This is a deliberate
  deviation from the byte-identical upstream tool, which Factory's own eleven-folder repository
  would otherwise fail; no other rule changed.
- **Checks re-run on the staged tree**: `tools/factory-tests` PASS with all 25 suites,
  `tools/knowledge/knowledge-check` PASS, `tools/knowledge/doc-links` PASS (93 links),
  `tools/repo-health/repo-health` OK (AGENTS.md 84 lines, 9 folders, 0 big files),
  `examples/compare_cohorts.py` and `validate_fixtures.py` exit 0, offline suite 33 tests OK.
- **`python3 -m unittest discover -s demo/tests`**: 39 pass, 8 skipped, one error:
  `test_real_long_named_process_is_detected` cannot spawn `ps` (`Operation not permitted`) under
  this session's sandbox. Environmental, independent of the change; it runs from a normal shell.

Not verified: no loop job was executed (`LOOPS_ENABLED` unset, no paid or headless run); the
`loops/` payload is imported and inventoried, not exercised.

## Factory v1.8.4 update applied — 2026-11-01

The owner asked for the 1.8.4 fix after a dsh session failed to reload (`session event at seq 29
message must have role "user"`). The release moves the 250k/300k gate to advisory on a harness the
plugin cannot reach a compaction service for, so the session is no longer held waiting for a human
to type `/compact`; it also drops Pi's refusal of its own window compaction.

- **Written by `tools/agents/template-update --ref v1.8.4` from the tagged checkout** (`fac8bcb`):
  the 27 contract files and `VERSION`; `--check` afterwards reports `0 file(s) differ from v1.8.4`.
- **New connector tools**: `tools/agents/connectors.py` (one contract/merge file list),
  `refs.py` (git-reference reader), `dsh-install` (tag-pinned desktop plugin) and
  `template-update`; the `.agents/skills/template-update` skill and the 1.8.4 knowledge sentences
  for architecture, compatibility, context safety and build-and-test.
- **Checks**: `tools/agents/adapter-check --self` PASS (27 connectors: 27 matching, 0 drifted,
  0 absent, 0 unwired, 0 invalid, 0 unidentified); `tools/factory-tests` PASS with all 27 suites,
  including the new `test_dsh_install.py` and `test_template_update.py`.
- **Live profile**: the desktop dsh profile already loads a 1.8.4 copy of the plugin at
  `~/.dsh/profiles/desktop/aeion-factory/`; the repository now matches that release.

Not verified: no dsh session was replayed from the new plugin in this run; the corrupt transcripts
(`session-2d8481df…`, `session-8accced1…`) stay on disk and were read for recovery, not repaired.

## Agora factory: safe circuit, capability keys, protected branches — 2026-11-01

The local factory that builds the forum from 100 Markdown specs grew the parts the owner asked
for after "comment se protéger des rogue AI".

- **Review circuit** (`demo/factory/review_circuit.py`): the author model and its family are
  excluded, vote 1 comes from a second family, vote 2 from a third; any reject, transport error or
  malformed answer holds the feature. The publisher now refuses a receipt with no circuit, an
  unapproved one, or fewer than two votes (`verified_receipt`, 8 tests in
  `test_factory_pipeline.py`).
- **Credential roles** (`demo/factory/keys.py`): `GH_BUILD_KEY` (read), `GH_API_KEY` (publish),
  `GH_RELEASE_KEY` (human release), `OPENCODE_API_KEY` (inference); `assert_only`,
  `assert_worker_isolated`, publisher refusal and start-up scrubbing. 18 tests in
  `test_factory_keys.py`, including a drift test against the committed root `.env.example`.
- **Stop-on-branch hand-off** (`demo/factory/boundary.py`): five written rules, the same five
  copied into `demo/flue/src/agents/coder.ts`, the brief written to `TASK.md` outside the clone,
  and `test_factory_boundary.py` proving both copies agree.
- **Product repository**: `.github/scripts/check_product.py` plus a `Product artifacts` job,
  merged as `develop@e79080ab` through PR #2 with green CI. `main` and `develop` now require a
  pull request, those five checks, linear history and resolved conversations, with force-push and
  deletion refused and admins included; a probe push to each branch was rejected by the server.
  PR #1, the simulated transport artifact, was closed and its branch deleted.
- **Checks**: 171 factory tests, then 232 in `demo/tests` with the one known macOS `ps`
  `PermissionError` in `test_openshell_setup`; `knowledge-check`, `doc-links`, `repo-health`,
  `factory-tests` (PASS, 27 suites) in the product clone; `git diff --check` clean.

Not verified: no live publish ran through the new publisher, and no model call was made for the
circuit — the OpenCode endpoint still has to accept the four model identifiers. The key roles are
enforced in code, not by GitHub: a token whose real permissions are wider than the table would not
be detected.

## Factory v1.9.0 update applied — 2026-11-01

Owner request: "make sure everyone is using the latest aeion factory template
<https://github.com/OualidGuennif/aeion-factory/releases/tag/v1.9.0>".

What v1.9.0 changes for a project: the 250k latch lets go. A verified handover releases the hard gate
instead of leaving every call denied, a handover that went stale can still be compacted, the receipt
survives the settlement, and the dsh plugin keeps its pending request when `PreCompact` refuses. For
this repository that is harness behaviour only: no product or knowledge document changes.

| Step | Command | Result |
| --- | --- | --- |
| What the release changes | `git show v1.9.0:CHANGELOG.md` (factory checkout) | compaction-latch fixes, no connector or policy change |
| Dry run, three groups | `tools/agents/template-update --ref v1.9.0 --root <repo> --check` | `1.8.9 → 1.9.0`, **one** differing file (`VERSION`); nothing to merge |
| Apply | `tools/agents/template-update --ref v1.9.0 --root <repo>` | `written VERSION → 1.9.0`; `knowledge/`, `work/`, `CHANGELOG.md`, `AGENTS.md` and the three settings files untouched |
| Connectors | `tools/agents/adapter-check --root <repo> --ref v1.9.0` | `27 connectors: 27 matching, 0 drifted, 0 absent, 0 unwired, 0 invalid, 0 unidentified, 0 unroled` → **PASS** |
| The repo's own checks | `tools/factory-tests`, `doc-links`, `knowledge-check`, `repo-health`, `git diff --check` | `14 tests OK`, 97 links, 0 problems, clean |

**A red check was fixed by the update, not by a local patch.** `tools/factory-tests` had been failing
on `test_a_steering_copy_fails_the_check`: the vendored test replaced the literal
`agent.steer({ id: globalThis.crypto.randomUUID(), content:` while the 1.9.0 plugin writes
`agent.steer({ id: ..., role: 'user', content:`, so the replacement was a no-op and the check exited 0.
Five factory-owned tool files were a release behind and were refreshed from the tag byte for byte:
`tools/agents/adapter-check`, `tools/agents/tests/{test_adapter_check.py, test_hooks.py, test_dsh.mjs}`
and `tools/context/tests/test_budget.py`. No project text was rewritten; the only project line edited
is the version in `AGENTS.md`, which named 1.8.4 and was therefore false.

Kept deliberately: this repository's own diagram in `tools/architecture/views.json` — which broke the
refresh contract and is repaired in the entry below — and the three-line local adaptation in
`tools/repo-health/repo-health` that keeps the generated passive `skills/` pool out of the hand-made
folder count.

## Release PR #9: the two red checks fixed at their cause — 2026-11-02

`offline-examples` failed with seven `AttributeError`s inside one test:
`demo/tests/test_sandbox.py` patched `openshell.SandboxClient`, but once another test module puts
`demo` on `sys.path` — the factory tests do, with `sys.path.insert(0, parents[1])` — `import openshell`
resolves to the `demo/openshell/` directory as a namespace package. The `skipUnless(openshell)` guard
was satisfied by that namespace package, so the test ran and then could not find the attribute; it
passed only while no such module had run first. The test now installs an inert stub module in
`sys.modules` whose constructor raises `AssertionError`: the refusal must happen before any client
object exists, and the test no longer depends on whether the SDK is installed. Local:
`python3 -m unittest discover -s demo/tests` → 341 tests, 1 error (the pre-existing macOS `ps`
limitation), 9 skipped; CI `offline-examples`: PASS.

`Graphify and Archify` failed before rendering anything: `tools/architecture/refresh` requires exactly
three views in `tools/architecture/views.json` — `architecture`, `workflow`, `lifecycle` — and the
v1.8.3 adoption had replaced them with a single custom view, so every refresh since then stopped at
"maintain exactly the overview, delivery and context views". The file now carries this repository's
overview (its twelve components each citing a source anchor that resolves exactly once) followed by
the v1.9.0 delivery and context views, whose anchors resolve unchanged in this tree. Local:
`refresh --target e4ed339 --base origin/main` → `validate: pass`, `deliver: pass`, `check: pass`;
`browser-check` cannot run inside the DSH macOS file sandbox (Chrome refuses to initialize its own
sandbox there). CI `Graphify and Archify`: PASS.

Both failures pre-date the v1.9.0 update and were invisible until this branch ran them: the workflow
had never executed against the single-view file, and the sandbox test had always been the first module
in a fresh interpreter.

## The forum in a browser, and the Langfuse address in the configuration — 2026-11-02

The owner opened the links and found two things missing: the forum answered `Resource not found` at
`/` (it is a JSON API; the front is the React Native app, which had never run anywhere), and the
Langfuse login address was only in the compose file and the README, not in the generated
configuration.

**The front now runs in a browser, unchanged, through `react-native-web`.** Three pieces:
`react-dom@19.3.1` and `react-native-web@0.21.4` (the first install picked `react-dom@19.3.0`
against `react@19.3.1`, and React refuses to boot across a patch difference — the error named both
versions); `src/api.ts` sends `credentials: 'include'` and lets the browser's cookie jar hold the
session, since a browser hides `Set-Cookie` and forbids a `Cookie` header; and the forum allows
exactly `http://127.0.0.1:8082` and `http://localhost:8082` with credentials
(`quarkus.http.cors.*`), because the cookie is `SameSite=Strict` and the page must keep the API's
host name.

| Claim | Evidence |
| --- | --- |
| The page renders and reads the forum | headless Chrome on `http://127.0.0.1:8082`: thread list from `/api/threads`, footer `release unreleased · runtime 25.0.4` from `/healthz` |
| The browser may open a session | `curl` with `Origin: http://127.0.0.1:8082` → preflight 200 with `access-control-allow-credentials: true`; login 200 with `Set-Cookie` |
| The browser may write | register 201, create 201 with the CSRF token, **403 without it** |
| The device path did not regress | `npm run typecheck` exit 0; `npm run smoke` 12/12; `expo export --platform ios` 1.5 MB Hermes bundle |

Not verified: no human has looked at the screen. Expo Go was installed on a booted iPhone 17
simulator and the project handed to it, but this Xcode ships no `Simulator.app`, so nothing was seen
there; the browser check is a headless screenshot.

**The Langfuse address now lives with the password.** `demo/setup.py` writes `LANGFUSE_EMAIL` into
`demo/.local/stack.env` next to `LANGFUSE_PASSWORD`, prints where both are, and `demo/compose.yaml`
reads `${LANGFUSE_EMAIL:-demo@aeion.local}` so an older configuration still boots. Verified by
running the script in an isolated copy: the key is written once and the other keys are unchanged.

## The external review, checked at its claim sites — 2026-11-02

An external review of this repository reports five defects and three product gaps, and asks for a
decision before acting. This run applied no plan; it read the cited sites and reproduced the
cheapest failures, so the owner decides on checked claims rather than on a summary.

| Claim | Check | Result |
| --- | --- | --- |
| F2, publish loader raises | `publisher.load_publish_credential()` with `gh_probe.load_secret` replaced by a no-op | `NameError: name 'for_role' is not defined`, before any credential is read |
| F1, review bytes are not bound | read `factory/artifact.py:88` and `factory/publisher.py:40-57` | the digest is SHA-256 over sorted **paths**; `verified_receipt` compares that digest and `base_sha`, never the content digest of the queued `files` |
| F3, valid votes score zero | read `factory/review_circuit.py:82` and `factory/models.py:52` | stored outcomes are `approve`/`reject`; the success set is `approved`/`rejected`/`passed` |
| F4, the diagnostic can serve | read `factory/live_readiness.py:30-36` and `demo/app/server.py` | `from server import sandbox_ready` inside the report; `server.py` calls `serve_forever()` at module level |
| F5, the release proxy cannot carry a session | read `demo/deploy/playground.py` | `do_GET` handlers only; `_forward` builds a GET and passes no incoming headers |
| G1, the builder is simulated | read `factory/api.py:28` and the `factory/dispatch.py` docstring | `profile=fake`, `mode=fake`, "fake inference and a fake forge" — stated, not hidden |

Not verified here: the review's receipt-forgery fixture was not replayed end to end, no remote
write and no secret read were attempted, and the cleanup and real-executor plans were not started.
The claim that `demo/forum/product/` is absent from the tree and that the 100 features still point
at it was not rechecked in this run.

## Plan A and B executed and verified — 2026-11-02

The owner approved plan v1 A/B/C and explicitly required the old Deno/Hono demo to be deleted.
This run removed it, repaired the five reproduced defects and verified each repair against the
live checkout. Plan C (one real forum feature build) was designed but not implemented; no paid
inference, publication, deployment or credential read occurred.

| Change | Check | Result |
| --- | --- | --- |
| A, old demo removed | `git ls-files demo/playground`; `grep 8090` in active app/config/docs | no tracked file, no service, no link or probe; `demo/tests/test_playground_removed.py` passes |
| A, running container | `docker ps` then stop/remove `aeion-observability-demo-playground-1` | removed; `http://127.0.0.1:8090/` returns `URLError` |
| A, operator entry | cockpit `index.html` | hero and nav link `/factory`; forum API/web rows in the demo runbook |
| F1, content binding | pipeline fixture: approve, then change one queued byte, keep all receipt fields | `verified_receipt` returns `None`; `Publisher` refuses `forged_content`; fake forge receives nothing |
| F1, unsupported effects | artifact tests | rename/delete/binary/unreadable held with `unsupported_effect:*` or `binary_content`; digest changes with bytes |
| F2, loader | empty secret loader, no publish key / fixture key | `CredentialError:credential_missing:publish` / token returned; CLI exits 2 without traceback |
| F3, vote labels | complete two-approve circuit | `n=1, success_rate=1.0` for both models; a malformed answer remains 0.0 |
| F4, readiness | `runpy` the diagnostic with `ThreadingHTTPServer` substituted | report produced, no server constructor call, `server` not imported |
| F5, proxy scope | fake upstream, direct vs proxy | direct cookie 200; proxy cookie 400; proxy POST 405; upstream saw only the direct cookie |
| Full suite | `python3 -m unittest discover -s demo/tests -v` | **366 passed, 9 skipped** |
| Knowledge | `tools/knowledge/knowledge-check`, `doc-links`, `repo-health` | PASS, PASS (97 links), PASS |
| Template | `template-update --from-ref v1.9.0 --ref v1.9.1 --check`, `adapter-check --ref v1.9.1` | 0 files differ; 27/27 connectors match; demo product checkout moved v1.8.6 → v1.9.1 and matches too |

The fix-verification script is temporary and lives at
`/private/tmp/aeion-observability-review-20261102-6lixqiw6/verify-fixes.py`; its output recorded
`F1 forged_content`, `F2 ran`, `F3 success_rate 1.0`, `F4 attempted_server_start false` and the
F5 statuses above. These are local mechanism checks, not a live harness, provider or Langfuse
ingestion proof.

## One pinned forum build through the real check and Langfuse — 2026-11-02

Plan C was implemented offline against the runnable Quarkus forum, not the planned
`demo/forum/product/` tree. The target profile names feature 013, base commit
`753ba3ed239560f2854921efb10530916dcc57ab`, the main/test write scopes, an adapted brief and a
protected Gradle check. The builder was an injected fake model and the forge was the fake forge:
no paid inference, publication, deployment or credential read occurred.

| Claim | Evidence | Result |
| --- | --- | --- |
| The base is exact and isolated | `target.materialize` clones `753ba3e`, verifies `HEAD` and a clean tree; `test_factory_target.py` | pass; clone under `demo/.local/factory/work/<build_id>/repo` |
| Scopes and brief come from the profile, not the 100-feature plan | `test_factory_target_dispatch.py`: catalog feature still says `demo/forum/product/`, artifact is accepted in the two Quarkus scopes | pass |
| The protected check is external | contract test lives in `demo/forum/targets/forum-app-013/`, outside both scopes; copied in, run, then removed | pass |
| The real Gradle suite passes | `gradle test --offline --console=plain --no-daemon` with `GRADLE_USER_HOME=demo/.local/gradle-home` | return code 0, 27,596 ms; contract SHA-256 `23706825…a07d` |
| A missing base holds | target replaced with a missing source | `base_unavailable`; no artifact, no publisher |
| A builder or check failure never publishes | injected exception / `exit 1` check | `FAILED`; no `publisher` field in the receipt |
| Identity reaches the receipt | live build `26b29b2f9fb34083b0a737fc92ec4766`, attempt `5518a5d638d34a848fcaf1df9915fa92`, artifact `6b78a27a…41b1` | all four ids plus `base_sha` present |
| Review circuit ran | two injected `approve` answers from different families; deterministic rules first | `approved`; publisher `published` (fake PR, no GitHub call) |
| Telemetry reaches Langfuse | `factory.build` span, trace `0ea7e7625fc2109a535817c6f7eeabdd` | read back with build, feature, attempt, artifact and session all matching |
| The cockpit can show it | live build is in `demo/.local/factory/factory.db`; `demo/app/factory.js` renders build/attempt ids and links `/trace/<id>` | `test_factory_board_link.py`; board row present |
| No paid run | injected builder and injected reviewer, `cost_reservation_usd = 0.00` | no model endpoint and no credential used |

Run: `demo/.local/venv/bin/python demo/tests/qualify_forum_build.py` → exit 0, `status:
completed`, `langfuse.status: PASS`. The same command with `--no-telemetry` passed earlier
(build `076aa7455c044f54a2f7ca2534d5d7e4`, 26,641 ms).

Honest scope: the model is fake by construction, so this proves the adapter, the protected
check, the identity plumbing and the Langfuse read-back — not model quality, a real pull
request or a production deployment. The target's `QuarkusTestDatabase` remains inside the
candidate test scope; a change to it would appear in the reviewed diff, and the deterministic
reviewer runs before the check. Moving the pin to a new base and one paid live run still need
the owner's decision.

## Product repo, two daily purses and local Docker — 2026-11-02

The runnable forum now has one canonical source, the separate
`OualidGuennif/aeion-autonomous-forum` checkout. The factory target was repointed, and the
local publish path was exercised without a paid model, a registry push or a VPS.

| Claim | Evidence | Result |
| --- | --- | --- |
| Product source is canonical | `demo/.local/factory/agents/aeion-autonomous-forum` at `37417ab`; commits `1224d03` (feature-013 filter) and `4e27f73` (Docker) | clean `develop`, local commits only, remote not pushed |
| The target clones the product repo | `demo/forum/targets/forum-app-013.json`: `target_repo = OualidGuennif/aeion-autonomous-forum`, base `37417ab` | `test_forum_target_profile.py` 5/5 pass |
| The offline build still passes from the product repo | qualification build `311a5ac3f4d74e1f8e7a3b2603d0b7b4`, attempt `95312667492045808ac9aa83baa79b5b`, artifact `6b78a27a…41b1`, base `37417ab` | Gradle return 0 in 28,292 ms; trace `94563192e3b5a34ecc6d8c421c3c173e`; Langfuse read-back PASS |
| Requalified after the product commits | build `b14c4283c3b14cce8684fdb94216f1e2`, base `37417ab` | gate passed, Gradle return 0 in 50,097 ms; same artifact digest |
| Feature 013 is in the product | offline qualification build `4e40fcff…` produced `SecurityHeadersFilter.java`; product test with the external contract | `gradle test` return 0 in 37 s, including `SecurityHeadersContractTest` |
| Two independent $15.00 purses | `demo/factory/budget.py`; `test_factory_budget.py` | reserve before, settle after; open reservations count; corrupt ledger fails closed; one scope cannot borrow from the other |
| A sub-cent reservation is not free | `test_factory_budget.py::test_a_positive_sub_cent_reservation_is_rounded_up_not_free` | $0.001 reserves $0.01 and settles at $0.01 |
| A free reservation cannot become paid | `test_factory_budget.py::test_a_zero_reservation_cannot_settle_a_positive_cost` | $0.00 reservation + $0.01 settlement raises `settlement_exceeds_reservation`; spend stays $0.00 |
| Protected check is confined | `test_factory_target_check.py::test_a_repository_outside_the_allowed_workspace_is_refused` | a repo outside the factory work root is refused before any copy or command |
| Review circuit families are distinct | `test_factory_publish.py::CircuitIndependenceTests`; `verified_receipt` | two votes in one family are refused; two families pass |
| Worker refusal is real | `test_factory_target_dispatch.py::test_an_exhausted_purse_holds_before_a_session_or_builder` | `HELD` / `budget_unavailable`; no session, builder or work directory |
| A worker without a purse also holds | `test_factory_target_dispatch.py::test_a_worker_without_a_purse_holds_before_any_work` | `HELD` / `budget_unavailable`; no work directory |
| The paid publish worker is pursed | `publish_once.build_worker`; `test_factory_publish_once.py` | forum purse, positive $0.10 reservation, unbudgeted path refused |
| Cockpit refusal is real | `test_triage.py::test_a_live_run_without_a_purse_fails_closed` (venv) | `failed` / `BUDGET_STOP`; no ledger entry |
| Full demo suite stays green | `demo/.local/venv/bin/python -m unittest discover -s demo/tests -v` | 426 tests, OK, 0 skipped |
| Docker image runs non-root | `aeion-autonomous-forum:local`, UID/GID `10001`, `eclipse-temurin:25-jre` | healthy on `127.0.0.1:8081` |
| Health and headers | `docker compose -f demo/forum-app/compose.yaml up --build -d`; `curl /healthz` and `/api/threads/not-a-number` | `{"status":"ok","release":"local-docker",…}`; 404; CSP `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`, `nosniff`, `no-referrer`, HSTS on both; report-only absent |
| No remote or paid action | fake builder and fake forge; no `docker push`, no provider call, no VPS command | confirmed; the image is local-only |

Honest scope: the feature-013 Java bytes come from the injected offline builder, not a paid model
run. The protected Gradle check is real and passed, but model quality and a real PR remain
unproven. The container is published only to loopback on this PC.

## Orphaned OpenShell sandboxes removed — 2026-11-02

The owner reported a large number of OpenShell sessions still running in Docker and consuming
CPU. The host had **nine sandbox pairs** (18 containers) created between 20:13 and 20:27 on
2026-11-01, all still up 14 hours later. The gateway's own record list was empty: these workloads
were orphaned, not active. The qualification that created them had no corresponding
`DeleteSandbox` requests for the leaked names, so the exact interruption point is not in the
gateway log; the observable failure is a cleanup path that did not run or did not finish.

| Check | Evidence | Result |
| --- | --- | --- |
| Orphans identified | `docker ps` with `openshell.ai/managed-by=openshell`; created timestamps 2026-11-01 20:13–20:27 | 18 containers (9 sandbox pairs); CPU 5–22% per supervisor |
| No gateway records | Python `SandboxClient.list(workspace="default")` through the qualified local client | empty page; removing the containers did not delete live state |
| Removal | `docker rm -f` on the 18 labeled containers only | 0 OpenShell containers remain; forum and Langfuse stack untouched |
| CPU after removal | `docker stats --no-stream` | OpenShell supervisors gone; remaining stack dominated by ClickHouse's normal background work, forum ~0.4–3.6% |
| Reaper selection | `demo/openshell/reap.py --older-than 3600` | dry run selects 0 now; test fixtures prove old-only selection and dry-run safety |
| Bootstrap hardening | `demo/openshell/setup.py` imports `reap` and sweeps older-than-1-hour labeled containers | `test_openshell_setup` and `test_openshell_reap` pass |

The safety window is one hour: a normal agent is bounded to 360 seconds × at most three agents,
and the harness qualification is shorter, so only abandoned pairs are eligible. The reaper is
host-side and never runs inside an agent sandbox; it only removes containers carrying OpenShell's
`managed-by` and `sandbox-namespace=aeion-observability` labels.

## Publication to main through PR #11 — 2026-11-02

The reviewed `develop` head was released to protected `main` through
[PR #11](https://github.com/OualidGuennif/aeion-observability/pull/11), never a direct push.
`main` requires linear history, so the release was a squash.

| Claim | Evidence | Result |
| --- | --- | --- |
| Released head is exactly the reviewed one | PR #11 `headRefOid` `0afe95bde6dc1ec4f15175d17128a0ba0b452f1d`; `.aeion/reviews/0afe95b….md` | `Review: OK`, also posted as a commit comment |
| Every check is green on that head | runs 41434142607 (`docker-demo`, `offline-examples`, knowledge health) and 41434142552 (`Graphify and Archify`) | all four `pass`; the `review` workflow skipped because it is not armed for this PR |
| The PR was mergeable | `gh pr view 11`: `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN` | no unresolved threads, base up to date |
| Merge is a squash, not a merge commit | `gh pr merge 11 --squash` | `main` = `3d9ae70abf78229414f3aed73fcc08f14897205e` |
| `main` carries exactly the released tree | `git rev-parse 0afe95b^{tree} origin/main^{tree}` | both `97285ec054dcbe8ca660e3555577060a4ed6739e` |
| `develop` does not diverge after the squash | `git merge origin/main` on `develop` | merge `fc795e3`; no content change |
| CI reached the local-only tests at their cause | `demo/tests/test_forum_target_profile.py` `setUp` skip | five profile tests skipped when the product checkout is absent; 426 tests OK, 12 skipped locally |

## Review coverage, trace delivery and the budget day — 2026-11-02

The first offline slice of the DeepSeek cockpit brief closes two truthfulness gaps that the
owner journey depends on: a review must never approve bytes its voters did not receive, and a
trace id must never be displayed as a delivered record. The budget day is now explicit.

| Claim | Evidence | Result |
| --- | --- | --- |
| An oversized review is held, not truncated | `test_factory_modelfarm.py::test_oversized_single_file_is_held_without_calling_a_model`; 20,000-char file | `held` / `review_input_too_large`; no model call |
| A tail file can no longer disappear | `test_factory_modelfarm.py::test_a_tail_file_never_disappears_from_the_review_envelope` | held before any vote; coverage lists both paths |
| An unknown author cannot start a review | `test_factory_modelfarm.py::test_an_unknown_author_cannot_start_a_review` | `held` / `author_identity_unknown`; no vote |
| An approval records complete coverage | `test_an_approved_circuit_records_complete_coverage` | `coverage.complete` true, files, 64-char content digest |
| A timeout holds the circuit | `test_a_timeout_holds_the_circuit` | `held` / `reviewer_failed` |
| A failed export is not "emitted" | `test_factory_telemetry.py::test_an_exporter_failure_is_not_reported_as_emitted` | `export_failed` / `exporter_returned_failure` |
| An exporter exception is evidence | `test_an_exporter_exception_is_recorded_as_a_failure` | `export_failed` / `ConnectionError` |
| A successful local export claims only that | `test_a_span_is_created_with_the_expected_attributes` | `exported_unconfirmed`, `confirmation=not_read_back` |
| The offline qualification still passes after the change | `demo/tests/qualify_forum_build.py`; build `1f5e916a…`, attempt `03e32bd7…`, artifact `6b78a27a…` | gate passed, Gradle 0 in 19.3 s, review approved, `exported_unconfirmed` |
| The read-back confirms that trace | Langfuse `GET /api/public/v2/observations?traceId=e0d6b3cc…` | PASS on build, feature, attempt, artifact and session |
| The budget day is Europe/Paris | `test_factory_budget.py::test_the_budget_day_is_europe_paris_across_midnight` | 23:30 UTC is the next Paris day |
| A default budget uses that day | `test_a_default_budget_uses_the_paris_day` | reservation recorded on `2026-11-03` |
| Full demo suite | `demo/.local/venv/bin/python -m unittest discover -s demo/tests` | 434 tests OK |
| Documentation | `tools/knowledge/doc-links`; `tools/knowledge/knowledge-check`; `tools/repo-health/repo-health` | PASS |

Honest scope: no real provider or browser acceptance ran for this slice. The offline qualification
did run its real Gradle check and a bounded Langfuse read-back: the exporter still reported
`exported_unconfirmed`, and the separate read-back supplied the confirmation. The cockpit does not
yet show that confirmation; the next slice wires it. The check environment still executes
candidate Gradle tests on the host (B6), so Live stays held.

## Factory v1.9.2 applied to both projects — 2026-11-02

The factory checkout was clean at v1.9.2 (`4417c68`). Both adopted projects moved from v1.9.1
with the factory's own `template-update` (the vendored 1.9.1 copy cannot update itself).

| Claim | Evidence | Result |
| --- | --- | --- |
| Only one contract file drifted | `template-update --from-ref v1.9.1 --ref v1.9.2 --root <project> --check` on both | `.pi/extensions/factory/index.js`, nothing else |
| Both write only that file | same command without `--check` | `written .pi/extensions/factory/index.js`; VERSION, knowledge/, work/, CHANGELOG.md, AGENTS.md and the other harness settings untouched |
| Connectors match the release | `/Users/wallseven/Desktop/AEion./aeion-factory/tools/agents/adapter-check --ref v1.9.2 --root <project>` on both roots. The adopted checkout has no `v1.9.2` tag, so the reference must be resolved from the factory repository; its vendored copy refuses the tag | 27/27 matching, 0 drifted, PASS on each |
| The 1.9.2 behavior is the new one | diff: the `tool_result` compaction block is gone; `Stop` now receives `observed_tokens` at `agent_before_settle`; a one-shot print run ends with a pointer to the verified handover | matches the factory 1.9.2 changelog |
| The vendored Pi test matches the connector | `tools/agents/tests/test_pi.mjs` refreshed from tag `v1.9.2`; it was byte-identical to `v1.9.1` before | `tools/factory-tests: PASS`, including the two settlement-compaction tests |
| The Pi README documents the new boundary | `.pi/README.md` refreshed from `v1.9.2` | states the clean one-shot stop and interactive settlement compaction |
| The application version is separate | root `VERSION` still `1.9.0`; adopted contracts are v1.9.2 | not overwritten, as the brief requires |
| Forum change is local | `ab72692` in `demo/.local/factory/agents/aeion-autonomous-forum` | committed, not pushed |

## One execution path for the browser — 2026-11-02

The front no longer has to fall back to the fake Markdown builder. `demo/factory/execution.py`
resolves an explicit mode, `FactoryApp` forwards the components to its worker, and the catalog
response tells the operator which execution is active.

| Claim | Evidence | Result |
| --- | --- | --- |
| Simulator is explicit, not a fallback | `test_factory_execution.py::test_simulator_is_explicit_and_has_no_target` | `{"mode": "simulator"}` |
| An unknown mode holds | `test_an_unknown_mode_holds_instead_of_guessing` | `execution_mode_unknown`, no builder |
| Offline without a profile or checkout holds | `test_offline_without_a_profile_holds_and_never_simulates` | `execution_unavailable`, no target or builder |
| A real pinned profile resolves | resolve over this repository: `offline`, target feature 013 | no hold |
| A pinned target cannot freeze another feature | `test_factory_target_dispatch.py::test_a_target_for_one_feature_never_freezes_another` | `target_feature_mismatch`; no work directory |
| The app holds every build when its execution is unavailable | `test_an_unavailable_offline_execution_holds_every_build` | `held`; no work directory |
| `FactoryApp` runs the real offline builder and check | `test_offline_execution_runs_the_real_builder_and_check` | `simulated_complete`, gate passed, Java files, no fake Markdown |
| The catalog reports mode, hold and the Live reason | `test_the_catalog_reports_the_hold_and_the_live_reason`; `factory.js renderExecution` | `offline`, hold, `live_builder_unqualified` |
| Full demo suite | `demo/.local/venv/bin/python -m unittest discover -s demo/tests` | 445 tests OK |

Browser entrypoint check: the server was started with `AEION_FACTORY_EXECUTION=offline` and the
API returned `{"mode": "offline", "target_feature": "013", "live_hold_reason":
"live_builder_unqualified"}`. Queuing feature 013 through `/api/factory/queue` was **held at
admission with `dependency_missing`**: the live store has no merged evidence for dependency 001,
and this change deliberately does not satisfy it with a simulation receipt. The offline
completion above ran through `FactoryApp.tick` with a fixture catalog whose dependency list was
empty; it is not evidence that the live dependency is satisfied.

Honest scope: no browser rendering, Live execution or dependency-baseline import is claimed. The
next step is a verified baseline for the product features already present at the pinned commit,
then the cockpit trace confirmation.

## Publication of the lifecycle slices through PR #12 — 2026-11-02

The reviewed `develop` work (review coverage, trace delivery, Paris budget day, Factory v1.9.2 and
the explicit execution path) was released to protected `main` through
[PR #12](https://github.com/OualidGuennif/aeion-observability/pull/12), again as a squash.

| Claim | Evidence | Result |
| --- | --- | --- |
| Released head is exactly the reviewed one | PR #12 head `bbb856892d9dded1e48d6a995704ed8faea9a1eb`; `.aeion/reviews/bbb85689….md` | first line `Review: OK` |
| Every required check is green on that head | run 41442808792 (`docker-demo`, `offline-examples`, knowledge health) and 41442808798 (`Graphify and Archify`) | all four `pass`; `review` skipped (not armed) |
| The PR was mergeable | `gh pr view 12`: `MERGEABLE`, `CLEAN` | no unresolved threads |
| Merge is a squash | `gh pr merge 12 --squash` | `main` = `3bef6439fb177d18a5cca2dd7948b85b1a93a539` |
| `main` carries exactly the released tree | `git rev-parse bbb8568^{tree} origin/main^{tree}` | both `890f5814e419166f36ed57f4f511b1e8da5cffdd` |
| `develop` does not diverge after the squash | `git merge origin/main` on `develop` | merge `deb9bdf`; no content change |
| The evidence names a runnable adapter check | corrected row: factory copy with `--root <project>` | 27/27 PASS on both roots |

## Isolated checks, baseline and one live build — 2026-11-02

The second implementation slice was exercised locally after the owner authorized paid inference
and named four workers (`glm-5.3-flash`, `qwen-3.8-flash`, `deepseek-4.1-flash`,
`claude-haiku-5.5`). No credential value or raw transcript was printed; the provider credential
was loaded by the application from the existing dotenv files.

| Claim | Evidence | Result |
| --- | --- | --- |
| Protected Java check runs in the isolated boundary | `demo/factory/isolation.py`; real 013 qualification | Gradle passed in 43 s inside `maven:3.9-eclipse-temurin-25`, image `sha256:93b8a14…`, `network: none`, non-root, read-only root, no Docker socket, toolchain caches read-only |
| A lost boundary holds, never uses the host | `demo/factory/dispatch.py`; `test_a_lost_isolation_boundary_holds_instead_of_failing_the_build` | **Fixed 2026-11-02:** `ProtectedChecks` nests the reason under `detail`; `_isolation_unqualified` reads it there and the build is held as `sandbox_unqualified` with no attempt id instead of ending `FAILED` |
| Contract tampering during the check is detected | `test_a_modified_contract_is_detected_and_restored` | `contract_modified`, original restored |
| Sandbox close survives seed, collection and agent failure | `demo/tests/test_runner_teardown.py` | three cases, one close each, no active sandbox left |
| Unknown usage cannot settle as zero | `Runner._settle`; `test_unknown_usage_keeps_the_reservation_open` | `settled_usd: unsettled`, reservation still counted |
| Two concurrent logins cannot reuse one bootstrap token | `test_concurrent_login_mints_at_most_one_session` | exactly one session |
| Display ids map to canonical wire ids | `test_wire_ids_are_the_documented_identifiers`; provider probe | `glm-5.3-flash` requested and accepted |
| 001 is a verified pinned-base baseline, not a simulation | `demo/factory/baseline.py --feature 001 --apply` | base `37417ab…`; five hashed paths; isolated base suite returncode 0 with the same image/probe; recorded build `09d2f736…` |
| 013 can now queue against that evidence | live store admission after the baseline | `queued`, no `dependency_missing` |
| One real paid build completes | build `5bd31768fd0b41d9a083776ae00baec6` | `live_complete`, `simulated: false`, gate `passed`, fake publisher `published` |
| Its check used the isolated boundary | receipt `gradle_test.detail.isolation` | `qualified`, image digest above, probe denied network and socket |
| Its trace reached Langfuse | trace `5d926786bd644df61b4e0fd97b349079`, observation `6a1becec6aeb6ef9` | `confirmed` via authenticated readback |
| Budget stayed bounded | shared ledger summary | 6 reservations, 6 settled, 0 open, provider-reported spend $0.00 |
| Full demo suite | `demo/.local/venv/bin/python -m unittest discover -s demo/tests` | 489 tests OK |

The first two live attempts failed the protected check on candidate-authored tests (an
absent-header matcher and a missing `@WithTestResource`), not on the contract; their receipts are
`failed` and their reservations settled at the provider-reported cost. An earlier successful
build `0a5eb2a6…` (trace `9aadae66…`) was stored but its immediate readback raced ingestion and was
reported `exported_unconfirmed`; a bounded retry now confirms it. The provider reported `cost: 0`
for these calls, so the ledger shows no dollars: that is a provider-reported amount, not an
invoice or evidence that inference is free.

Honest scope: no browser login/session was performed by the agent, the cockpit was started in
`live` mode and served `/factory` with the catalog endpoint requiring a session; review votes are
not yet budget-reserved; the pricing-profile expiry gate is not yet shared with the factory
router; the Product repository/spec ownership separation and OpenShell reaper lease reconciliation
remain.

Independent review of `e2e8e12` (2026-11-02) then returned **NOT OK** with four confirmed
defects, so that head is not evidence that the slice is publishable: a `..` component could pass
the live builder's textual scope check and write `.git` bytes invisible to `git diff`; a failed
second live call reused the previous `last_usage`; the isolation hold read the wrong result
nesting; and a failed paid builder kept a stale author model in its receipt. The follow-up commit
fixes all four with regressions: `parse_files` rejects every `.`/`..`/`.git` component before the
scope prefix check (`.GIT` included), `LiveBuilder` resets `last_usage` before each call,
`_isolation_unqualified` reads the nested reason so a lost boundary holds the build, and
`_take_builder_state` refreshes the author (and paid usage) before a `builder_error` receipt. The
suite is 489 tests OK. A fresh independent review of the new exact head is still required before
any push.

## One eligibility authority for the four workers — 2026-11-02

`demo/factory/models.py` now owns the eligibility facts for the four owner-authorized workers
(authorization date `2026-11-02`, recorded profile name and expiry), and
`demo/app/profiles.py` asks that catalog instead of keeping its own `valid_until`.
DeepSeek's harness profile expired on 2026-10-31; the owner's spend authorization on 2026-11-02
does not renew a provider qualification, so the router, the builder and the app all refuse it
until it is requalified and dated forward. GLM, Qwen and Haiku stay eligible under the recorded
authorization.

| Claim | Evidence | Result |
| --- | --- | --- |
| The app and the factory agree on DeepSeek | `profile_available('deepseek')`; `eligibility('deepseek-4.1-flash')` | both false, reason `profile_expired` |
| The router never selects it | `Router().select('review')`; `eligible()` | absent from both |
| The live client refuses it before transport | `test_an_ineligible_model_is_refused_before_transport` | `model_ineligible:profile_expired`, zero transport calls |
| The other three remain eligible | `test_the_app_and_the_factory_read_one_eligibility_verdict` | GLM, Qwen, Haiku selectable |
| Full demo suite | `demo/.local/venv/bin/python -m unittest discover -s demo/tests` | 491 tests OK |

Honest scope: Qwen and Haiku have no harness profile record; their eligibility basis is the
dated owner authorization, not a provider requalification. DeepSeek needs a fresh profile
verification (account, region, protocol) before it can be enabled again.

## Second independent review and the boundary fixes — 2026-11-02

An independent model review (`glm-5.3-flash`, a different family from the implementer, given
the exact `origin/develop..HEAD` diff and the review checklist) returned **NOT OK** for
`eaca6d2`. No raw prompt or answer was retained or printed. I verified every finding:

| Finding | Verdict | Correction |
| --- | --- | --- |
| The Docker runner qualified an image digest but executed the mutable tag (`isolation.py:137`) | **Confirmed** | The probe and every check now run `image_id`; a re-tagged or re-pulled tag cannot execute bytes the probe did not qualify. `test_execution_runs_the_qualified_digest_not_the_mutable_tag` |
| An intermediate symlink inside a scope could redirect a write to `.git` (`live.py:110`) | **Confirmed** | A resolved target must stay inside the *resolved matched scope*, not only inside the repository. `test_an_intermediate_symlink_cannot_redirect_a_write_outside_the_scope` |
| A deleted contract surfaced as `toolchain_missing` (`checks.py:127`) | **Confirmed, lower impact** | A missing destination is now `contract_modified`; the outer handler already prevented a stranded build. `test_a_deleted_contract_is_tampering_not_a_missing_toolchain` |
| `app.profiles.available` could raise `ImportError` (`profiles.py:20`) | **Not confirmed** | `server.py` inserts `demo/` into `sys.path` before any request can call `available`; no path reaches the deferred import without `factory` importable |
| Unreported cost keeps a reservation open forever (`dispatch.py:190`) | **By design** | The brief requires unknown usage to remain an outstanding liability and forbids settling it as zero; the provider reported `cost: 0` for the calls used here |

Full demo suite after the fixes: 494 tests OK. Review-call budgeting: four `$0.25`
reservations were opened for the four independent-review attempts; the attempt that returned
the verdict and the attempt whose provider-reported cost was measured `0` are settled, the two
whose usage is unknown stay open. `aeion-observability` shows `$0.50` outstanding and `$14.50`
remaining for 2026-11-02; that is journal liability, not an invoice.

## Re-review at 13a1470 and the container/probe fixes — 2026-11-02

The independent model re-review of `13a1470` verified the digest, symlink and contract fixes
and returned NOT OK with four findings. Two were false on inspection: `dispatch.py` already
imports `Decimal` and `InvalidOperation`, and `app/relay.py` defines and sets
`last_error_code`. Two were confirmed: a timed-out `docker run` client left its container
running with the workspace mounted, and the probe passed `-e SENTINEL=` itself, so its
`host_environment: absent` claim was untested. The runner now names every check container and
removes it on timeout or interruption, and the probe carries the sentinel only in the client
environment and asserts it is absent inside the container. 496 demo tests OK; the review call
settled at the provider-reported `0`. Outstanding review liability remains `$0.50` from the two
calls whose usage is unknown.

## Review votes are budgeted per call — 2026-11-02

`DispatchWorker` now wraps each review vote in its own reservation: `$0.05` from the product
purse before the call, settled only with that call's measured complete usage, and left open
when the callback reports none. `demo/factory/live.py` adds `LiveReview`, which keeps the
provider's usage surface for the budgeted wrapper, and `execution.resolve("live")` injects it.
Evidence: `test_each_vote_reserves_and_settles_its_own_usage` (reserve + settle at `$0.02`),
`test_an_unknown_vote_keeps_its_reservation_open` (`$0.05` still counted), and
`test_a_configured_review_circuit_reserves_each_vote_and_keeps_them_open` (build plus two votes,
none free), and `test_a_raising_callback_cannot_settle_the_previous_votes_usage` (the wrapper
clears `last_usage` before each call, so a failure keeps its own reservation open instead of
settling the previous vote's cost). Full demo suite: 500 tests OK.

## Develop publication and the release pull request — 2026-11-02

`develop` was pushed at `f677e1a` with an exact-head `Review: OK` receipt for the full delta
and at `3069ad1` with the per-vote review budget receipt; both receipts are posted as commit
comments. [PR #14](https://github.com/OualidGuennif/aeion-observability/pull/14) is open against
`main`. GitHub reported it `DIRTY` because the squashed PR #13 changed the same two work files,
so `origin/main` was merged into `develop` keeping this branch's newer entry; the conflict was
only in `work/current.md` and `work/validation.md`, and no code changed in the merge. The demo
suite is 500 tests OK and the cockpit runs in `live` mode at `http://127.0.0.1:8088/factory`
(`/factory` 200, catalog 401 unauthenticated); the owner logs in with the private token file,
which the agent did not read.

## Host-only CI can import the teardown path — 2026-11-02

PR #14's `offline-examples` job failed on `ModuleNotFoundError: tokenizers` while importing
`app.runner` for `test_runner_teardown`. The dependency was imported at module scope in
`token_budget.py`, although only `TokenBudget` construction needs it. Both `jinja2` and
`tokenizers` now load inside `TokenBudget.__init__`; the runtime counting tests check that the
pinned wheels are importable before they run; and the runner's failed-span status tolerates a
host without the OpenTelemetry SDK instead of failing the run after the verdict. Evidence:
`python3 -m unittest discover -s demo/tests` on the bare system interpreter (no jinja2, no
tokenizers, no opentelemetry) -> 500 tests OK, 12 skipped; the demo venv -> 500 tests OK, no
errors. This is the host-only job's environment, so the check should go green on the next push.

## Release PR #14 merged to main — 2026-11-02

`develop` head `7c6a775` passed `docker-demo`, `offline-examples`, `Graphify and Archify` and
`Knowledge, links and repository health` on [PR #14](https://github.com/OualidGuennif/aeion-observability/pull/14).
The release review (`.aeion/loop-bodies/review-14.md`) recorded `Review: OK` for that exact head
and was posted on the pull request; the squash merge is `main` `6d76c99555fef3f90ce951b4bd516083c921d2e3`.
`origin/main` was merged back into `develop` as `2f04111` with no conflict, and
`git diff origin/main..HEAD` is empty: the two branches carry the same tree. The PR body and
the review name what is not in this release: OpenShell reaper lease reconciliation,
repository/spec ownership separation, and browser acceptance with the owner's session.

## The OpenShell reaper waits for confirmed absent leases — 2026-11-02

The reaper selected orphan candidates from the two OpenShell labels and the age window alone. A
live build's sandbox can legitimately outlive that window, so a bootstrap sweep could remove a
running sandbox; and a store that could not be read was indistinguishable from "nothing runs".
`demo/openshell/reap.py` now reads the factory store (`demo/.local/factory/factory.db`, read-only
SQLite URI) and holds the sweep while any dispatched build lease is still live, or while the store
exists but cannot be queried. Four states decide it: `absent` (the factory never initialized, so no
build can hold a lease, and the sweep proceeds), `idle` (no dispatched lease, sweep proceeds),
`active` and `unknown` (blocked with `build_lease_active` / `build_lease_unknown`). Containers are
listed before the lease is read, so a lease claimed in between is seen by the gate, while a sandbox
started after the listing cannot be in the removal set; removal runs only after that read.
`--execute` exits 1 when the gate held, and the bootstrap prints only what it removed. The store
path follows the file location (the demo tree), so the automatic bootstrap sweep keeps working,
and `--store` names a different state directory.

Evidence: `demo/tests/test_openshell_reap.py` (9 tests) covers the four lease states, the boundary
where `lease_until_ns == now` is expired, a held execute with zero `docker rm`, an unreadable
store and a directory in place of the store refusing execute, an absent store proceeding, and the
untouched dry-run/staleness behaviour. Full demo suite in the demo venv: 504 tests OK.
`python3 demo/openshell/reap.py --older-than 3600` against the real store reports
`leases.state: idle`, zero candidates, exit 0.

An independent model review of the exact code diff (`glm-5.3-flash`, a different family) returned
`OK` with no findings. Re-reading before committing still found one fail-open path: `Path.is_file()`
returns false on a stat error, so a store present but not stat-able would have been reported
`absent` and the sweep would have proceeded. Presence now uses `stat()`: `FileNotFoundError` is
absent, any other `OSError` is unknown. That is the difference between "the factory never ran" and
"I cannot read the lease store", and the directory regression above pins it.

Limit, stated rather than hidden: the gate is global because check containers carry no attempt
label, so one live dispatch holds the whole sweep instead of protecting only its own sandbox. That
is fail-closed for cleanup; per-container reconciliation needs the attempt identity on the
container, which the isolation runner does not pass yet.

## The product snapshot has one owner and a drift check — 2026-11-02

`demo/forum-app`, `demo/forum-db` and `demo/forum-mobile` are the input of the factory's baseline
hash, the feature-013 target and the Compose packaging, but the canonical source is the separate
`aeion-autonomous-forum` repository. The 53 tracked files were byte-identical to that repository's
`37417ab` (`git show 37417ab:<path>` compared to the working tree for every file), yet nothing
stopped a hand edit from silently becoming this repository's product.

They are now declared as a read-only snapshot: `demo/forum/source.json` pins the repository and
commit, `demo/forum/source.lock.json` records a SHA-256 per file, and `demo/forum/source.py` is the
contract. `--check` (the default, and a step of the knowledge CI job) compares the tracked working
tree to the lock and fails on a missing, changed or extra tracked file; it needs only this
checkout. `--refresh --product <checkout>` re-copies the pinned commit after refusing a dirty
snapshot, and reads blobs with `git ls-tree`/`git cat-file` rather than `git archive` because the
product repository marks `/demo` `export-ignore` (an archive-based copy silently produced no
files). The product checkout may be ahead: refresh reads the pinned commit object, never a
checkout or branch, and never pushes.

Evidence: `demo/tests/test_forum_source.py` (7 tests) covers the repository snapshot matching its
lock, a hand edit, an extra tracked file, refresh restoring the pinned bytes while dropping a stale
file, a dirty snapshot refused (`mirror_dirty`), a product checkout without the pinned commit
(`product_commit_missing`), and a symlink in the product snapshot refused
(`product_entry_not_a_file`). `python3 demo/forum/source.py --check` reports `ok: true`, 53 files.
Full demo suite: 511 tests OK. The five local product commits (`ab72692` head) are untouched and
unpushed; publishing them remains the owner's decision.

## PR #15 merged to main — 2026-11-02

[PR #15](https://github.com/OualidGuennif/aeion-observability/pull/15) carried `cc671e4` (the
reaper lease gate), `ae42ed9` (the pinned product snapshot) and `3660d09` (the task record) from
`develop`. Its head `3660d09e1d13ba07b16575e4d6c9c998ee2ba482` passed `docker-demo` (2m11s),
`offline-examples` (21s), `Graphify and Archify` (34s) and `Knowledge, links and repository
health` (7s, including the new `demo/forum/source.py --check` step); the `review` check is a
skipped template job. The squash merge is `main`
`0098c04f4570da731c520d518c3053ee101b59a3`; `origin/main` was merged back into `develop` as
`0d49c9f`, so the two branches carry the same tree. The pull request body names what it does not
include: browser acceptance with the owner's session, and publishing the product checkout's five
local commits. Post-merge `CI` (run `41471821925`) and `Architecture refresh` (run
`41471822171`) both succeeded on `0098c04`.

## Æion Factory v1.9.3 connectors — 2026-11-02

Release `v1.9.3` adds one connector: `tools/agents/pi-rpc`, the headless Pi RPC runner behind
`tools/agents/run pi rpc` (one `pi --mode rpc` process, so a settlement compaction and its resumed
run finish together). `tools/agents/connectors.py` lists it and `tools/agents/run` dispatches to
it. The factory changed no merge file, so no project text was proposed.

`/Users/wallseven/Desktop/AEion./aeion-factory/tools/agents/template-update --from-ref v1.9.2
--ref v1.9.3 --root /Users/wallseven/Desktop/AEion./aeion-observability` reported exactly three
files (`run`, `pi-rpc`, `connectors.py`) and wrote them; `VERSION`, `knowledge/`, `work/`,
`CHANGELOG.md`, `AGENTS.md` and the harness settings were left alone. `adapter-check --root
/Users/wallseven/Desktop/AEion./aeion-observability --ref v1.9.3` reports 28 connectors, 28
matching, 0 drifted, 0 absent, 0 unwired, 0 invalid, 0 linked, 0 mode: PASS. `pi-rpc --help`
renders; `tools/factory-tests` PASS; demo suite 512 tests OK; doc-links PASS (97); knowledge-check
PASS; repo-health PASS.

The vendored factory-owned tools were then refreshed from the same tag: `tools/agents/adapter-check`,
`tools/agents/template-update` (now `--from-ref`), `tools/factory-tests`, and
`tools/agents/tests/test_adapter_check.py`, `test_hooks.py`, `test_template_update.py`,
`test_dsh.mjs` and the new `test_pi_rpc.py`. `adapter-check` still reports 28/28 PASS,
`tools/agents/template-update --help` shows `--from-ref`, and `tools/factory-tests` PASS. The
project-adapted `tools/architecture/views.json` and local `tools/repo-health` adaptation were left
untouched on purpose.

## Usable feature cockpit and feature-specific dispatch — 2026-11-02

Owner scope: improve the confusing local cockpit, prevent selecting/relaunching completed
features, unblock actual unmet work and make failures recoverable. This is a local controller
delivery. No forum implementation was written by hand, and no model call, push, merge or remote
deployment was made by this task. Concurrent Factory connector and product changes were preserved.

Root `/` and `/factory` now serve one operator cockpit; `/lab` retains the advanced model lab.
Search, phase/status filters, ready-work selection, recent real builds, collapsed simulations,
receipt details, trace confirmation and the shared daily budget have distinct presentations. The
release drill is loaded only when opened; displaying the cockpit does not start it. An existing
authenticated session obtains its CSRF value from the authenticated board after a page refresh.

Availability comes from persisted supervisor records. Merged/baseline features are implemented;
real completed candidates are separately labeled as awaiting integration. Both, and active jobs,
are disabled and refused by admission. `BEGIN IMMEDIATE` serializes the read/insert across Store
instances, same-key replay is retained, and a mixed conflicting batch admits nothing. Simulation
does not establish implementation or fulfill a real prerequisite.

The live resolver loads validated per-feature profiles instead of applying target 013 globally.
The dispatcher uses the selected target's base, brief, scopes and protected check. Missing targets
hold before reserving money. Unexpected worker exceptions persist as `worker_error` holds and do
not silently freeze unrelated queued work or automatically repeat a potentially paid call. Paid
builders now require the existing independent review circuit by default.

Feature 017 is the next configured unmet feature. Its profile pins canonical product commit
`b0201db86135b943e84e9fececbde87dbaa7d36e`, not the old pre-013 base, and injects the external
`RequestValidationContractTest.java` only through the protected check. On a disposable clone, the
real Docker check compiled and ran Gradle in 41,734 ms, then returned 1 as expected: unknown
registration fields and missing/wrong-type fields were accepted by the current product. The
oversized-body and existing valid-shaped authentication cases passed. This is evidence that work
is missing, not that feature 017 has already been implemented.

The boundary used immutable image
`sha256:93b8a14ea2f412782e4e842651273b4d903e35cc496284f178fbbe2d67d00976`, denied network,
read-only root, uid/gid 65534, no capabilities, no Docker socket/host environment, 3 GB memory,
2 CPUs and 512 PIDs. Contract SHA-256:
`60c2ff0fd1b003f9774d431f0be74f6cb3f4a2df8f9e5772b5d216e901faba7d`.

Verification:

- `test_cockpit_admission.py`: 9 passing tests for persistent completion locks, simulation,
  same-key replay, competing Store instances, atomic batches, catalog availability and HTTP 409.
- `test_factory_feature_targets.py`: 6 passing tests for distinct targets through one FactoryApp,
  catalog availability, trusted resolution, unsupported work before budget, worker-error recovery
  and paid review requirements.
- `node --test demo/tests/test_cockpit_client.mjs`: 6 passing client tests; `node --check` passes.
- Final `knowledge-check`: PASS (0 problems); `doc-links --diff origin/develop --worktree`:
  PASS (105 links); `repo-health`: PASS; `git diff --check`: PASS. The 9 admission and 6 target
  regressions were also re-run against the final working tree and passed.
- `python -m unittest discover -s demo/tests -v` in a sanitized temporary source snapshot:
  527 discovered, 522 passed, 5 checkout-specific skips, exit 0 (30.817 s). Those 5 profile cases
  were then run against the actual checkout and all passed, without inference or Gradle work.
  Local raw output: `/private/tmp/aeion-cockpit-final-20261102-nowfa5s9/demo-tests.log`.
- Real browser fixture using the shipped HTML/CSS/JS and FactoryApp presenters: 017 can be checked
  and enables Build selected; 001 and 013 checkboxes are disabled. Verified at the default desktop
  width and 390px; document width equals viewport width (390px), with the launch control enabled.
  The fixture visibly states that it contains no provider or real builds. No build button was
  clicked. Its temporary server was stopped, its tab closed and viewport override reset.
- The actual controller was reloaded only after an atomic SQLite preflight found zero queued or
  dispatched jobs. Root responds 200. Read-only real-state availability: 017 ready, 001/013 locked,
  97 requiring a target/prerequisite. Restart invalidated its in-memory browser session; final
  authenticated acceptance and the real 017 attempt remain owner actions. No admin token was read.

Manual sensitive-diff review followed the `security-scan` skill: browser IDs cannot choose a
repository/command/path, target files are trusted and validated, feature/target equality remains
checked, SQL values are parameterized, receipt text is escaped, trace IDs are constrained, and
existing loopback/session/CSRF, isolation, budget and unknown-usage guards remain. No new service,
dependency or widened privilege was added to the product. No native external scanner or independent
model review was run; this is a local boundary review with regression evidence.

Remaining scope is explicit: 97 catalog entries do not yet have runnable contracts; checked
candidates are not automatically integrated; a successful paid 017 build and its Langfuse readback
have not been claimed. The lifecycle handoff records incremental contracts and trusted integration
as the follow-up, without re-enabling unsupported checkboxes or pretending the catalog is executable.

## Full code pass and monitored live feature 017 — 2026-11-02

The owner subsequently authorized a full code pass and a real feature launch. Full scope, defect
proofs and exact attempt/artifact/trace identities are in the
[assessment record](full-pass-live-feature-2026-11-02.md). Earlier no-paid-call statements above
describe the previous UI delivery, not this later explicitly authorized live check.

Confirmed and fixed with failing-before/passing-after regressions: duplicate claims between
Store instances, completion/cancellation races, automatic requeue after an uncertain interrupted
attempt, too-short worker leases, lost held-attempt identity, malformed queue values escaping as
TypeError, and the 60-second authoring timeout. Final transitions now serialize with SQLite
`BEGIN IMMEDIATE`; expired attempts hold rather than spend again; held requests need explicit
cancellation before retry; authoring has a 180-second transport timeout and reviews keep 60 seconds.
Builder failures also emit bounded trace evidence. No new dependency/service/privilege was added.

Final fresh source snapshot: `/private/var/folders/71/5ylk1yz559s8pdrf5r4t71sw0000gn/T/aeion-full-pass-20261102-5_8qbybd`.
`python -m unittest discover -s demo/tests -v`: 535 tests, 530 passed, 5 local-checkout skips,
exit 0 in 30.810 s. The 5 `test_forum_target_profile.py` cases passed separately on the actual
checkout. Examples: 33 passed; Flue: 14 passed; cockpit client: 6 passed; `tools/factory-tests` PASS.
The 5 recovery tests, 25 live-client tests and 7 feature-target tests passed against the working
tree. No claim that this proves every provider or candidate implementation succeeds.

Preflight: empty real queue, clean canonical product at
`b0201db86135b943e84e9fececbde87dbaa7d36e`, target 017 present and Docker boundary qualified
with the same immutable image/denied-network evidence as above. The logged-out browser was not
bypassed: the owner's local queue admission used the existing Store operator API, no administrator
token read. Controller picked up each job through its normal FactoryApp/DispatchWorker loop.

Actual outcomes, all with backend-confirmed Langfuse failure traces:

| Build | Result | Trace |
| --- | --- | --- |
| `c4c67c272ac748a99e39f26513503034` | Author timeout, no code/check/review | `f5f44fd55f2833bfa38b124a27c9b367` |
| `af511eaca2b1496b8d6303db74731a3a` | Generated code refused by Java compilation: unsupported enum | `a11f280923869e0807443344c8d7a5ca` |
| `87655cb326db471d86d34bba92393851` | Compiles; 2 external and 4 own validation assertions fail | `9aa21fadcf879d124bbff0d05462c3ca` |

The final candidate strips `/` from the route before looking it up in a map whose keys retain `/`.
It therefore bypasses its own validation: the isolated contract observed 201 instead of 422 on
an unknown registration key, and 400 instead of 422 on missing/wrong-type fields. This was in a
disposable test database. No candidate was approved, integrated, published or deployed; the
canonical product remains unchanged. No reviewer call occurred. A pure local coverage check
also found 7655 chars against the complete-review limit of 6000; no approval on an excerpt.

Three authoring reservations of $0.50 were made; two calls have provider-reported settlements,
the initial timeout keeps its unknown-usage $0.50 reservation open. The forum purse ends at
$1.00 counted including prior work and open liabilities, $14.00 remaining, not a billing invoice.
No queued/dispatched job remains, and no further paid attempt was made after the third failure.

Feature 017 remains unimplemented. The brief and lifecycle handoff retain the verified toolchain,
route-normalization and review-size constraints. The next builder task is a focused repair,
followed by the unchanged external acceptance and two-family review; none of those gates was
disabled to make a build pass. Authenticated browser acceptance remains unavailable while logged
out; native external scanner/independent model-audit coverage was not claimed.

## Direct implementation of the report with Codex — 2026-11-02

The owner explicitly requested direct implementation after the failed live attempts above.
The [repair record](feature-017-codex-repair-2026-11-02.md) supersedes that pending status.
Feature 017 is now implemented in canonical product local commit
`a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`; its working tree is clean. The independent external
contract was unchanged. Before: 58 Java tests, 6 failures; final repair: 58 passing. The exact
commit passed protected Gradle again in 40892 ms and a replay in 38069 ms under the same immutable
qualified Docker boundary. No schema/dependency change or manual edit of the read-only snapshot.

Baseline `2716fe2bb1044ceabdecdcc6f4e38513` records the exact base, source/test hashes and external
contract hash. A replay returned the same build ID. Its recovered metadata-only Langfuse trace
`18fe0c7e99f4af1cb8d78278cf42d7f9` is confirmed by backend readback (observation
`9951e9bf4653582e`). Actual store availability is implemented/selectable=false. A new-key launch
probe was refused as `feature_already_completed:017` without creating another row; the queue is
idle. The earlier three failures and unknown-usage liability remain intact.

Report fixes: bounded compiler identifiers displayed escaped in the client; complete review
envelope 24000 chars with refusal/no calls above it; legacy `run_features.py --live` refused before
work and separate fixture state; preserved macOS path aliases in Docker arguments; curated 017
baseline checks its own external contract; proof/trace visible in baseline receipts; baseline
verification idempotent despite new timing, without superseding active requests. The CLI's local
queue.py shadowed stdlib queue and broke urllib3 on missing LifoQueue; reproduced in a subprocess,
then fixed and verified through the successful real trace replay.

Final isolated demo suite: 544 tests (539 passed, 5 local-checkout skips), exit 0, 31.181 s.
The five local profile cases passed separately. Examples 33, Flue 14, client 7 pass. Snapshot/logs:
`/private/var/folders/71/5ylk1yz559s8pdrf5r4t71sw0000gn/T/aeion-full-pass-20261102-z64ew5n0`.
Controller knowledge/doc-links (105)/health/diff checks pass; product repair-delta checks pass
(99 links). Snapshot drift check: 53 files, no change. The controller reloaded only after an atomic
no-active/no-queued preflight and root returned 200. No paid model call, remote push/deployment,
forged independent review, or restart of the running forum image occurred in this repair.

The browser connector could list the existing tab but could not attach to it; authenticated
visual acceptance is not claimed. The genuine persisted outcome and client behavior are verified
separately. Other catalog contracts/model quality benchmarking and forum image rollout remain
distinct work, not implied by this successful code baseline.

## Owner-authorized local clean restart — 2026-11-02

The owner subsequently requested a clean local restart. The nine observation containers,
native controller and gateway were restarted without deleting volumes or resetting state.
The exact committed product was packaged offline through the qualified Docker runner and its
new local runtime image was started with the same forum data volume. The canonical product's
web front now runs on loopback 8082; HTML and its 1754456-byte JavaScript bundle return 200.
Feature-017 live API refusals return the expected 422 paths; the global body cap returns 413.
The front/API credentialed CORS check, anonymous catalog refusal (401), four integration health
checks and gateway mTLS health pass. Budget ledger SHA-256 and build history are unchanged;
the existing 017 trace is confirmed again. No paid model call or remote publication occurred.

Actual availability remains 0 selectable, with 001/013/017 completed and only 013/017 execution
targets configured. The advanced Flue lab still reports live/sandbox readiness false; gateway
health is not fresh sandbox qualification. Browser connector attachment remains unavailable.
See the [restart record](clean-restart-2026-11-02.md) for image identity and scope limits.

Documentation checks after the operation: knowledge-check PASS (0 problems), doc-links PASS
(105 links), repo-health PASS, git diff whitespace check PASS. The protected read-only product
snapshot still has 53 files with no drift; the canonical product Git working tree is clean.

## Feature 007 connected to real operator execution — 2026-11-02

Owner request: connect new feature execution from the cockpit. Added pinned target 007 and an
external Java sanitization contract. The unmodified pinned base runs 59 tests and fails exactly
the 5 new acceptance cases; an isolated injected candidate passes 59/59 through the actual
catalog/CSRF queue, bounded author prompt, artifact gate, Docker check and synthetic two-family
review path. Its result is simulated_complete in temporary state, not a real implementation
record. The external contract SHA-256 is
`c77e99036530853a9e933731f94d930304c2cab88eb0772e06d1004e2e0f273a`.

The author now receives complete bounded public Java context from the pinned commit, rather
than only a brief. Source paths, regular blobs, per-file/total bounds and full-brief refusal
have 11 regressions. Before the change the new context tests failed; after it all pass.
Targeted verification: 174 Python cases pass, including 7 real-checkout profile cases. Full
public-source snapshot verification: 557 demo cases, exit 0 (7 local-checkout skips already
covered separately), 33 examples, 14 Flue cases and 7 client cases pass. Knowledge-check (0),
doc-links (108), repo-health, whitespace and the protected 53-file snapshot drift check pass.

Idle preflight and reload succeeded (PID 40317, root 200). Actual persisted readiness now shows
007 ready/selectable with no missing dependency, while 001/013/017 remain locked. Real history
and budget ledger hashes are unchanged; no real queue admission, model call, publication or
product edit occurred. An initial full-suite authorization attempt hit the automatic review
service's usage limit; later activation and full-suite calls were approved normally.
See the [wiring record](feature-007-cockpit-wiring-2026-11-02.md) for exact scope and limits.

## 100-feature Quarkus/PostgreSQL/React web catalog — 2026-11-03

Owner explicitly chose Quarkus/Java, PostgreSQL product storage and React web with no native
mobile target, then requested compact specs in chronological order. Reviewed all six canonical
files and every ID; [100-row assessment](forum-catalog-review-2026-11-03.md). Updated architecture,
plan, current handoff and factory contract, then regenerated all 100 MDs, index, schema-v2
manifest and review snapshots. Four obsolete renamed files were removed by the generator.
Stable IDs/history remain unchanged; topological `sequence` is a separate display field.

Measured: 100 features, 342 dependency edges, 354–637 words/MD (median 397), three explicit
feature-specific steps each. Size counts: 46 S, 53 M, one L (the data migration). Changed shared
architecture hashes propagate into every feature/spec/catalog identity after regeneration.

Fresh checks:

- `python3 -B demo/forum/tools/generate_features.py --check`: PASS, exactly 100 up-to-date MDs.
- `python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v`: 21 PASS, including
  complete topological order, old-stack refusal, scope/parallel isolation and safety prerequisites.
- Manifest/board/admission tests: 11 + 4 + 10 PASS. Completed-feature launch locks remain active.
- `node --test demo/tests/test_cockpit_client.mjs`: 8 PASS, including sequence sorting without
  mutating stable IDs or bypassing availability.
- `tools/knowledge/knowledge-check`, `tools/knowledge/doc-links`, repo-health: PASS (110 links).
- `git diff --check`: PASS at inspection.

Broader public-source snapshot `aeion-full-pass-20261102-6kga7ouu`: examples 33 PASS, Flue and
client PASS at that snapshot; the full demo suite was **not green** (560 tests, 8 failures,
55 errors, 7 skips). Many errors are restricted loopback/process operations, plus a missing
synthetic image setting in a new sandbox test. Failures also include unfinished live-engine
qualification/profile/tokenizer/selection changes from the ongoing engine replacement.
This broad run is not cited as successful validation or attributed to the catalog change.

No product source or database was modified, no data volume deleted, no paid model called and
no GitHub write performed for the catalog revision. PostgreSQL migration/restore, React product
browser acceptance and the complete Flue-to-main path remain separately unqualified. Previously
pinned 007/013/017 profiles cover the older product base, not the changed product architecture.

### Flue native review repair and real local harness proof — 2026-11-03

While continuing the factory replacement, isolated synthetic review probes failed before any
upstream inference. The pinned SDK implementation showed three integration requirements:
Anthropic's model URL must be the relay origin (the SDK adds `/v1`), Pi uses the exact beta
path `/v1/messages?beta=true`, and the supervisor must supply the stable OpenCode conversation
header on the native Anthropic path. Fixed these boundaries, kept the upstream endpoint fixed,
refused arbitrary query variants, and preserved explicit adaptive/medium admission for Haiku.
The provider regression failed before the URL fix and then passed. Unknown/multimodal context
on the new conservative byte-bound profiles is refused rather than counted as plain text.

Fresh verification:

- Flue unit suite: 15 PASS, including native URL/session regression.
- `test_provider_protocols.py`: 4 PASS using only local fake upstreams, including arbitrary-query
  refusal and missing-medium refusal before transport.
- `test_runtime.py`: 7 PASS with real local tokenizers and fake loopback transport; existing
  test-resource warnings remain visible. No model provider was contacted.
- `demo/.local/venv/bin/python demo/tests/qualify_factory_flue.py`: **exit 0** on real Flue/Pi,
  real no-host-mount OpenShell, real protected Java/Docker checks and scripted local inference.
  Isolated state: `/private/tmp/aeion-real-flue-factory-fhw_rzxc`.
  Build `7c7858167b7540b5abd9b1f9578a009e`, trace `6cfc53021a12ac88a04d3c2feae55e0e`.
  The author used GLM's protocol, six requests and two fresh sessions with a hashed handover;
  the first protected check failure reached the agent, its repair passed, and the independent
  final Java check passed (41.112 seconds, contract `237068252f1b316e2d11590647c84e89d13131d491ff38225c3bdf9d50e6a07d`).
  Qwen and DeepSeek's separate Flue reviewers both approved the complete 1651-character artifact;
  a separate Haiku harness probe passed with adaptive thinking and medium effort. Twelve total
  fixture requests, no remote model calls; provider-reported **synthetic** cost is zero and native
  estimates are not invoices or model-quality evidence. The terminal state is correctly
  `simulated_complete`, with a fake forge, never a real main merge.

No factory activation marker was written. Persistent measured routing, isolated publication/
required-CI/confirmed-main and automatic current-contract preparation remain unfinished.
This proof uses the historical product target and does not qualify PostgreSQL/React migration.

Cockpit reload: idle preflight found zero active lab runs/campaigns and zero queued/dispatched
factory builds; only the verified owned controller was reloaded (PID 56672, root HTTP 200).
The new process reads the regenerated catalog. Existing build/budget records were preserved;
administrator sessions are in memory and must be renewed after controller restart. Authenticated
visual acceptance was not performed.

## Single scheduled continuation — 2026-11-03

Owner requested one resume at05:00 Europe/Paris today. Wrote, fsynced and verified
`work/HANDOVER.md` (15547bytes at scheduling, SHA256
`d1d88aa78b7ea7a11e1055eeefde227ab19823a0b02c209cc0d808fe7d4a8340`).
Created active thread-attached heartbeat `reprendre-la-factory-flue-5-h` with one occurrence
(COUNT1) at05:00. Tool returned Created and an ACTIVE id; its view card was opened. No daily
recurring continuation or extra thread was requested. The prompt resumes the already-authorized
implementation from the handover, preserving model/credential/budget/isolation gates.

Final handover readback after recording the automation ID: 15723bytes, SHA256 `ce89be5feca26c9fa610466e22d3cee05ee1ab713277d929e74733a67385999a`; fsync and readback verified.

## Scheduled continuation: automatic Java preparation and durable factory controls — 2026-11-03

The unique05:00 Paris heartbeat fired and was deleted through automation_update; no recurring
job was created. The factory activation receipt remains absent. No real inference or remote
GitHub write ran; owner data, product source and budget liabilities are preserved.

Implemented persistent routing/progress, frozen atomic publication with isolated role outbox,
confirmed-main-only completion, late-effect cancellation locks, complete MD/acceptance/artifact
review and a shared typed Flue preparer. Removed the obsolete direct model engine and CLIs.
Unknown outcomes/no-forward failures do not fabricate model quality; invented prior quality
scores were removed. The cockpit shows exact holds, chronological MD previews, role/evidence,
PR/CI details and main SHA without enabling an unqualified engine.

A protected-check parent symlink swap was reproduced deleting only a disposable synthetic
canary. Both pre-execution overwrite and post-execution cleanup paths are now confined;
regular nofollow bounded reads and frozen-acceptance checks have regression coverage.

Real automatic Java mechanism proof: `demo/tests/qualify_factory_preparation.py` exited0 with
actual Flue/Pi/OpenShell and isolated Java evaluation, scripted local inference/fake forge only.
State `/private/tmp/aeion-real-preparation-abv32f9m`, build
`ffc6191870304f03bfc52f2c7c3832a9`. Qwen prepared; GLM built across2sessions and repaired a true
protected-check failure; DeepSeek and Haiku approved independently, all4distinct identities.
Final Java gate37.402s;12synthetic inference requests; terminal simulated_complete. This uses a
historical Java/SQLite source and deliberately scoped disposable MD, not all100 contracts or
PostgreSQL/React acceptance. New JUnit assertion-type and role-memory changes require final rerun.

All3 native lab tiers also passed again with scripted inference: OpenShell6requests/2sessions/
12checks, local5/1/12, in-memory5/1/8. The lab cli qualification receipt cannot activate the factory.

Metadata-only integration probe made zero provider requests. Exact claude-mem and Hindsight
stored JSON readbacks confirmed; Hindsight document
`aeion-demo-synthetic/run-d5f07bf37a2d4cbb808b9f8c148a1710`. Its running1.1.0 Compose hash
`8bcb308f30cb99f75d732fa26d2e5defb7e28f0d28369cb95e6082772c9aa6e8` matches the declared
LLM-disabled/chunks configuration. Immediate Langfuse read was too early (probe exit1); a later
read of SAME trace `683d9bab4e0b12b7cf928c14ba3ab5b6` confirmed demo.task/task.passed,
observations `ba0f449e41dfd460` and `cfe3cc071a5c362c`. This is stored telemetry proof, not model
quality or paid-provider proof. Memory outages remain visible; retry replay is still pending.

Public-source snapshot `aeion-full-pass-20261102-gtdb_dn5`:586demo tests OK(7skips),33examples,
15Flue and14client. Later snapshot `...-t80lurvu`:601demo tests with2obsolete fixture expectations
failing; both fixed, feature_targets7 PASS. Current targeted preparation9, protected-check15,
role-memory2, publication-state10 and circuit/vote tests pass. Flue17 and client14 pass. Final
full-current-tree and docs/sign-off checks remain to run; do not present a stale full pass.

Read-only GitHub refresh: main remains `7193f5c95d7ce2db75ca9e5535ab5fe15e3cf237`, no PRs;
required Product artifacts CI job is absent. Each isolated build/publish/release role got403 on
GET main protection. An owner question about Administration read-only for release is pending;
no security permission was changed. Bootstrap/CI, PostgreSQL/React check adapters, current-MD
baseline/completion identity and a real protected merge remain unfinished. The cockpit backend
has not been reloaded in this continuation; actual user tab4 showed Sign in required.


## Current-contract evidence, isolated PostgreSQL and real UI actions — 2026-11-03

Owner continuation implemented in the observer; the actual product remains clean at
`a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`. No real provider request, GitHub write or product
migration occurred. Live factory activation remains absent.

- Release key protection GET200 now succeeds after the owner's Administration read-only change.
  Strict checks/admin enforcement are true, all five required contexts have Actions app15368.
  No credential value was read or displayed; a named loader consumed the one key privately.
- `test_factory_contract_identity.py`:12PASS, including failure-before-fix rewritten MD/deps,
  captured-byte race, symlink drift, explicit no-attempt supersession, uncertain attempt locks,
  historical SQLite migration and late merges preserving two contract versions. Exact feature
  metadata/MD/architecture now binds completion, dependencies, frozen receipts and publication.
  Unrelated catalog edits do not revoke unchanged contracts. Legacy baseline CLI cannot stamp
  new PostgreSQL/React requirements with an old SQLite proof.
- `test_factory_publication_http.py`:3PASS with REAL publish/release child processes and local HTTP,
  isolated fake keys/receipts/forge: exact-head CI wait across restart; cancel after green CI
  before merge; lost merge response reconciled by readback with exactly one PUT. This proves the
  mechanism, not a GitHub PR, hosted CI run or real main merge. Production has no fake endpoint flag.
- Gradle build/settings/properties/wrappers/version catalogs were wrongly approved by the old
  dependency rule. Regression failed before the fix; review and publisher now share one list.
 14review,18publisher and14key-role tests PASS. Templates accurately describe isolated release,
  Administration read-only and the limits of same-actor fine-grained PAT capability separation.
- Native `qualify_postgres.py` exit0, evidence `/private/tmp/aeion-postgres-proof-xgqbsnoy/proof.json`:
  PostgreSQL17.11, image `sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f`,
  RAM-only data, no host mount/port/external route, non-root checker over owned loopback. Real
  SQL transaction rollback, fresh second database, denied egress and confirmed removal after
  success AND candidate failure. Four unit boundary tests PASS. Initial startup failed at the
  entrypoint's temporary Unix socket; the actual diagnostic identified `/var/run/postgresql`,
  which now has its own bounded tmpfs. The PostgreSQL product migration adapter is not qualified.
- Native automatic MD preparation exit0: `/private/tmp/aeion-real-preparation-97dzczx_`, build
 `32ded74cf7f64729a48e570277955a9b`. Qwen preparer2calls, real failing baseline JUnit assertion;
  GLM author6calls/2OpenShell sessions with check failure→repair→handover; DeepSeek2+Haiku2 reviews.
  Protected final Gradle38938ms PASS, complete MD/acceptance/artifact envelope3750chars. Terminal
  is `simulated_complete`,12scripted inference calls, real provider0, fake forge. Scope is one
  custom Java/SQLite013 fixture, not the canonical100/PG/React/provider efficacy.
- All four roles' exact claude-mem and Hindsight documents confirmed. Fresh Langfuse readbacks
  of those SAME traces confirmed roots: prepare`7629ec472f7fbf0267d3cc074e2e884c`,
  author`ea9c27999a0cbd2fba25a3db73003387`, DeepSeek`7112db4c57dde49d85d23e63e720a03c`,
  Haiku`b1a3c0ff35eb3cab1697abaa2c9f64df`. Only basic/metadata queried; no prompt/source export.
- Current native `qualify_flue.py` exit0: tier3 OpenShell6requests/2sessions/12checks, tier2
  restricted local5/1/12, tier1 memory5/1/8.16scripted requests, real provider0. This refreshes
  LAB qualification only. No factory activation receipt was issued.
- Browser QA used the actual HTTP Handler, FactoryApp and current static files with three
  disposable fixtures, a distinct cookie and no worker/provider/owner secret. Login, literal
  hostileMD, selection, completed/dependency locks, queue+selection clearing, duplicate lock,
  cancel→ready and reload verified. Found/fixed misleading simulator execution promises and
  invisible queued/publication counts. [Screenshot](evidence/cockpit-fixture-2026-11-03.jpg).
  The temporary tab/server were closed; the owner's browser/session/token was untouched.
- A concrete [trusted CI patch](product-ci-bootstrap-2026-11-03/README.md) adds required Product
  artifacts and includes demo product sources in SAST. It applies to local a50, parses as YAML,
  new action revisions/pins/read permissions/commands verified. UNPUBLISHED; hosted CI and the
  bootstrap source integration still need real review and protected PR/main evidence.
- Full public-source snapshot `.../aeion-full-pass-20261102-th_5maw7`:629demo tests OK,7skips;
 33examples OK;17Flue tests OK;16client tests OK. This snapshot includes the final contract,
  publication subprocess, dependency policy, template, checker DI and client changes. The earlier
 617snapshot failed one outdated fixture expecting a web-profile refusal after mutating an
  already frozen catalog; the fixture now declares web scope before admission, preserving the
  intended refusal test. No assertion was weakened to accept a stale contract.
- Knowledge/doclinks/health PASS,112links at last check; manual security boundary review and
  regression evidence, no proprietary scanner or independent assistant-review claim.
- Live controller safely reloadedPID11582 after idle lab/campaign/factory checks and a private
  SQLite backup. HTTP200; all25build IDs/statuses/attempt generations preserved, budget ledger
  hash unchanged, SQLite quick_check=ok and new contract schema loaded. Factory remains paused.
  Memory-only admin sessions require local re-login; no token was read by the assistant.

Remaining: actual reviewed product bootstrap/CI into main; PostgreSQL migration/restore and
React/browser acceptance/toolchains; bounded approved build/dependency transition policy and
full artifact coverage for imports/locks; real provider/task evidence; actual protected publication
readback before activation. Current Java adapter holds001/002/003 and web scopes. Native PG
transport is not a completed cutover. No second wakeup/recurrence was created.


## Complete bootstrap reviews, Chromium and role separation — 2026-11-03

Owner authorized the complete backend/CI export to GLM+Qwen and the forum$15/day budget;
continued Chrome/security research was explicitly requested. No assistant subagent, new
schedule, product source change, GitHub write or factory activation occurred.

- Frozen bootstrap:49files168878bytes, sourcea50d607, base7193f5c, digest
  `15085ae47f150d429a291b55e6090eefa0e7ca10d69823eee6dc445d7b9d7d67`.
  Both v3 and fresh v4 passed knowledge/link/health/factory checks and actual offline Docker
  Gradle test+Quarkus packaging, non-root/cap-drop/read-only/no network; check.json binds bytes.
- First GLM call ended without a vote at4096output, actual provider resource cost0.01068027USD.
  Failure retained. Complete170062-byte synthetic packets now reach real Flue/Pi exactly once,
  without oversized argv; supervisor-only output extension16384 is admitted, default4096 and
  hard300k/context reserve unchanged. Native GLM/DeepSeek transport fixtures pass with local
  scripted inference only. Qwen's conservative byte counter correctly refuses before transport.
- Real GLM retry approved the complete bundle:4calls,176851input/5959output,
  resource cost0.02141263USD. Qwen refused locally,0forwarded/cost0. No second approval exists.
  Budget journal reports forum$0.05 rounded settlement/$14.95remaining and observer$0/$15.
- Fresh Langfuse metadata readbacks confirmed all three traces, including the initial failure:
  `d5c794b150eff8861d3ed279b4ab924a` (1generation),
  `637d356374a35281fd2340c5ec6d9319` (4generations),
  `10fb607c7e2aad11e61a2e182edfa1fc` (0generations).
  Exact Hindsight documents were freshly read back; claude-mem checkpoints confirmed during
  execution. No raw input/output requested. Proof: ignored bootstrap/v4/telemetry-readback.json.
- The one-hour v3 lease expired while other work continued. Controlled recovery verified all
  prior costs closed, no publication request, unchanged source/base/files/coverage and a fresh
  authorized attempt; fenced v3 through Store.cancel and carried the exact approval to v4.
  No lease extension, erased failure or unknown-liability retry.9bootstrap tests pass, including
  rejection of unreconciled costs. The second-model export question remains unanswered.
- Native Chromium sandbox qualification passed:156.0.8078.80, namespace/PID/network/Seccomp-BPF/
  TSYNC enabled; Yama absent. Non-root,zero effective capabilities,no-new-privileges,read-only,
  no host mount/port/key,external network denied and browser interaction passed. Proof:
  `/private/tmp/aeion-chromium-proof-cb60uewh/proof.json`; primary sources/profile provenance and
  fresh-build/verifier separation are in [research](chromium-security-2026-11-03.md).
- Trusted checker image inspected/executed at86d317a9…: Node26.13.0, OpenJDK25.0.4.1,
  React/DOM19.3.1, TypeScript5.9.3,Vite8.3.5,Vitest5.1.0,Playwright1.64.1. Public lockfile
  `npm audit --package-lock-only` exit0,0known advisories; no product source/private npm config sent.
- Fixed disposable PostgreSQL's shared owner credentials: fresh random admin/migration/app
  roles; the candidate receives only app credentials. Native PostgreSQL17.11 proves reads/writes,
  refusal of table/drop/temp/database/role DDL, rollback,fresh second DB and cleanup after failure.
  Proof: `/private/tmp/aeion-postgres-proof-ua2lxxhw/proof.json`. Audit-specific product grants,
  actual Flyway migration/import/restore and React/API acceptance are still unqualified.
- Activation regression reproduced9 failing subcases before fix. A Java-only, synthetic-main,
  malformed or missing PG/React receipt now refuses activation;4tests pass. Architecture bytes
  participate in the protocol hash. No qualification marker was created.
- Final source-only safe snapshot `/tmp/aeion-full-pass-20261102-_liai49b`:644demo tests OK
  (7explicit dependency/environment skips),33example tests,18Flue tests and16client tests pass.
  Snapshot includes new/untracked files but no private state/credentials; knowledge,doclinks120,
  repo-health pass. Root doclinks112 + diff/worktree and whitespace checks also pass.
- Manual boundary review covered frozen review coverage,budgets,expired-attempt fencing,credential
  delivery,PostgreSQL grants,Chromium namespace/seccomp and protected-main activation. No proprietary
  claude-security scan or hosted CI is claimed. These tests do not qualify the new product yet.
- Fresh reads: live cockpit PID11582/HTTP200, product localclean a50d607, actual GitHub main7193f5c
  protected,0open PRs. Actual migration/React adapters,second independent review,PR/CI/main and
  final activation remain open. No completed merge is claimed.

## Bootstrap quorum, measured budget repair and permission hold — 2026-11-03

This checkpoint supersedes the preceding section's pending DeepSeek question, single approval
and older output/budget limits. The owner authorized DeepSeek4.1 for the complete bundle, then
asked for a less restrictive per-execution budget within the already approved hard$15/day.

- The frozen49-file168878-byte backend/CI bundle is unchanged at digest
  `15085ae47f150d429a291b55e6090eefa0e7ca10d69823eee6dc445d7b9d7d67`,
  sourcea50d607/base7193f5c. Fresh v5 isolated Gradle tests/Quarkus packaging and repository
  checks passed. It imports the existing SQLite baseline; PostgreSQL/React remain unimplemented.
- Two actual independent complete approvals exist: retained GLM5.3Flash and DeepSeek4.1Flash.
  DeepSeek run`72d6bc9da102496880c1ce2356889182`, trace`0df6ab42703e51b357c37971a61ead41`:
  2forwarded requests,146092input/61908output,resource cost0.07087032USD,normalmedium/high
  effort,65536output ceiling,$1 execution ceiling. This is a provider resource cost, not an invoice.
  The forum journal is$0.22 rounded settled/$14.78 remaining, observer$0/$15; no paid run is active.
- Retained DeepSeek failures:16k default and low both OUTPUT_LIMIT at0.01950246USD each;
  low32k BUDGET_STOP at0.04482747USD. Low effort alone did not solve truncation. Confirmed root
  cause: relay accumulated worst-case output reservations without settling unused liability after
  measured responses. It now retains the larger of resource cost and conservative full counted
  input plus actual output price; unknown/unfinished usage retains the full bound. Three regression
  cases cover repeated admission, incomplete usage and higher reported cost. No failure was erased.
- Complete review packets are supplied once with the typed review tool; the reviewer has no
  emulated shell/filesystem fallback. DeepSeek native compatibility enforces explicit effort;
  enum-only effort metadata is cohort-separated with profilev3. Historical memory shape is retained.
  Native170062-byte/high65536 transport qualification passed with scripted inference,0real calls.
- New transactional worker-lease checks refuse expired completion and publication staging.
  Two regressions failed before the fix, then passed. Temporary source-repo fixtures now disable
  hooks/automatic maintenance locally after one retained pack-cleanup race; no global Git setting
  or drift assertion changed. The asynchronous writer's origin was not conclusively identified.
- Isolated real publication stopped at the first tree operation:held/tree_create_failed:403.
  No branch, commit, PR or merge was created. Before asking the owner, two valid same-blob tree
  probes returned201 and exactly the existing tree SHA, changing no ref/content; Contentswrite
  works. Missing permission for the changed CI workflow is the supported inference, not a token
  scope readback. The root publisher template/runbook now document temporary repository-only
  Workflowswrite for this reviewed maintainer bootstrap. Ordinary workers still cannot edit CI.
- Owner replied that they are outside and will activate that permission later. Publication stays
  held until their explicit activation reply: no GitHub action, model call, timer or automatic
  polling occurred after that reply. Two approvals remain saved; no retry was locally rearmed.
  The new explicit `resume-publication` phase checks unchanged main, exact stored request and
  branch/PR absence with reads, then transactionally rearms only the known effect-free403.
  Cancellation, changed payload, active lease and uncertain effects refuse recovery. Focused
  bootstrap12/publication-state13 tests passed; credentials load before claiming publication.
- Fresh local Langfuse metadata readback confirmed the final DeepSeek2generations; the exact
  Hindsight document matches run/trace and high effort. claude-mem confirmed during execution.
  Ignored v5/telemetry-readback.json retains earlier six traces plus this success; no raw source,
  prompt, output or reasoning was requested. All DeepSeek attempts total0.15470271resource USD.
- Final source-only safe snapshot`/tmp/aeion-full-pass-20261102-c8qd5ih_`:656demo tests OK
  (7explicit skips),33example tests,19Flue tests and16client tests passed. No private state,
  credentials or real provider is used by that suite. Root knowledge/doclinks112/health and
  whitespace checks passed. Product worktree remains clean at a50d607; activation marker absent.
  Snapshot checks include new files:knowledge/doclinks120/health passed. Its broader whitespace
  check found two extra EOF blanks (removed) and two required space-only unified-patch context
  lines in the frozen CI evidence patch (preserved); source whitespace passes excluding that patch.
- Local sensitive-change assessment covered immutable retry inputs, generation/lease fencing,
  unknown side effects, role-separated credentials and measured liability settlement. It is not
  an independent review of the observer changes or a proprietary claude-security scan. No new
  hosted CI result or protected merge is claimed. The two model votes cover only the frozen
  product bootstrap. Remaining: real PR/CI/main after owner activation, PostgreSQL migration/
  restore/audit grants, React/API/browser acceptance, bounded dependency transitions and the
  missing trusted source synchronizer before future tasks can freeze current remote main.

## Qwen launch policy, real bootstrap merge and source synchronization — 2026-11-03

Owner explicitly rejected the byte-estimate context refusal and confirmed publisher Workflows
activation, then asked to keep going. The earlier owner-away wait is resolved.

- Closed-tokenizer Qwen/Haiku profiles now use the Unicode byte bound for cost reservation
  only. Bounded requests launch; complete API usage gates the next request, with Anthropic cache
  reads/writes included. Unknown usage holds, native250k hands over and actual input+output
  above300k fails. These profiles do not have independent first-request300k preflight proof.
  Pinned-tokenizer preflight, budgets, role isolation and output/step limits remain enforced.
  Profilev4 separates this changed method from older routing evidence. Seven focused tests
  reproduced7failures before correction and all7passed after, including exact-counter refusal,
  unknown usage, cached context and actual overrun. Native Flue/Pi received170062bytes exactly
  once per request with Qwen-shaped scripted inference:2requests,0realprovider,typed vote,no shell.
- Workflows permission fixed actual tree creation. v5 published PR3/head906e8ad. Hosted backend
  tests/package and3security scans passed, but L3 doc-diff and Graphify failed. Local
  `doc-links --diff 7193f5c --worktree` reproduced the unchanged build-and-test spec failure;
  architecture refresh separately requires its owning spec to change with runtime/config.
- v6 retained all49previous files byte-for-byte and added only the2owning documents:
  51files198356bytes,digest`6d56126eb021ea98a4448789a68d292d05f4e0267d5515275b6eac7603ccf04d`.
  Both base documents match public aeion-factoryv1.8.6 SHA256 exactly; only709new documentation
  bytes describe existing approved CI/product boundaries. Initial automatic approval review
  rejected sensitive egress as a changed bundle; after these local/public checks, re-review
  allowed the same GLM/Qwen command. No alternate transport or bypass occurred.
- v6 doc-diff/knowledge/health/factory checks and isolated Gradle tests+package passed. First
  local check failed because its isolated PATH lacked Node; check-missing-node-path.json retains
  the failure. The corrected Node PATH passed; failed-check receipts now include bounded stderr.
  The trusted Docker checker mounts candidate workspace/public read-only tools/cache; it has no
  host environment/key/socket/egress, runs non-root/cap-drop/read-only with resource limits.
  This checker differs from untrusted OpenShell workers, which have no host mounts.
- Two NEW full real approvals bound the changed v6 bytes. GLM:3requests,151910input/7679output,
  resourceUSD0.02000821,run`6f676bb5416648ba9488d610114ea749`,
  trace`3981e6d8d34863839b823d8b7310350b`. Qwen:4requests,223982totalinput/8918output,
  resourceUSD0.04935952,run`8a340347a2dc4ebea82f78699df893f0`,
  trace`c7d24c2ec34bd24b59e8a06a094a5964`. Input totals sum requests, not peak context.
  Exact Langfuse generation counts and Hindsight run/trace readbacks passed; both claude-mem
  checkpoints confirmed. v6/telemetry-readback.json contains metadata only. No raw reasoning
  was requested. Journal:$0.30rounded forum settlement/$14.70remaining; observer$0/$15.
- [PR4](https://github.com/OualidGuennif/aeion-autonomous-forum/pull/4), head932c352, merged
  through the isolated release role into protected main`63bdece8056136209e0e3d2e68dbf0879005fec9`.
  All5required exact-head checks and the additional Graphify/Archify check passed; the optional
  review job is explicitly skipped, not counted as a success. Fresh readback confirms merged
  PR/main; v6/remote.json and ci-readback.json preserve proof. No direct/force push or protection
  change. Obsolete PR3 was closed only after exact-head verification; v5 was cancelled/fenced,
  with failures, approvals and branch/history preserved (v5/superseded.json).
- Added the previously missing source synchronizer before live MD freezing. Only a short-lived
  build/read-key child fetches the fixed repository into a unique temporary ref; ancestry and
  conditional update-ref protect origin/main. It never checks out/resets/stashes, writes remote
  refs, copies secrets to files/argv or inherits inference/publication keys. Unknown fetch, remote
  rewrite or concurrent ref change holds before spend. Temporary refs are removed; TLS verification
  and no redirects are explicit. Five real local-Git regressions plus preparation integration pass.
  Native actual build-key readback fetched main63bdece while preserving local HEADa50d607 and all
  worktree status; source-sync-readback.json records0model calls. The source file is protocol-bound.
- Final safe snapshot`/tmp/aeion-full-pass-20261102-mljlys95`:670demo tests OK (7explicit skips),
  33examples,19Flue,16client passed. No private state/credentials or real provider in that suite.
  Protocol binding/TLS flags were tightened afterward; focused checks cover those final changes.
  Local sensitive-change assessment traced measured-context admission, credential boundary,
  frozen-byte publication, stale-source/cancellation/concurrent-ref paths. This is no proprietary
  scanner or independent review of the observer diff; the two model votes cover only the product.
- Remaining product controls: real PostgreSQL migration/import/restore and audit grants, React
  production API/browser path, bounded build/dependency transitions and obsolete-file handling.
  All existing main product bytes remain the SQLite baseline. Factory activation stays absent;
  no existing volume/database was read, migrated or deleted. No new timer/subagent was created.


## Detailed operational checkpoint and shallow-source regression — 2026-11-03

Owner explicitly requested a detailed `work/current.md`. Replaced ambiguous historical/current
mixing with fifteen bounded entries carrying Owner decision, State, Next (agent), Blocker and
Evidence. Records actual product PR4 merge separately from pending observer main, exact source
identities, reviewer runs/traces/costs, context/counting limitations, budget, test snapshots,
PostgreSQL/React qualification gaps, cockpit work, security hypothesis and ordered resume steps.
The first prose draft failed knowledge-check because mandatory entry fields were missing; the
final version retains the detailed content in the established schema rather than weakening the check.
`HANDOVER.md` points to the new checkpoint, preserves the previous text as historical and carries
its SHA256. Both files were fsynced and read back exactly. No credential/transcript was read.

The pending `base_checkout_failed` was reproduced against actual product main63bdece. Source and
fresh clone are shallow; source has the commit in origin/main while the fresh clone advertises
only local develop/a50d607 and lacks the main object. This is verified object/ref evidence, not an
assumed permission problem. Added a real shallow clone fixture that fetches new main while keeping
local HEAD old and dirty/untracked operator files; it FAILED on the old materialize implementation
with `base_checkout_failed`. Fix fetches only the exact missing SHA from the local source, without
updating a branch or FETCH_HEAD. A failed-fetch test proves incomplete-clone cleanup and fixed error
without private Git diagnostics.

Verification after correction:
- `demo/.local/venv/bin/python -m unittest discover -s demo/tests -p test_factory_target.py -v`:10PASS.
- Same command with `test_factory_preparation.py`:11PASS; `test_factory_source_sync.py`:5PASS;
  `test_factory_qualification.py`:4PASS. Total30 focused checks; no full-suite rerun for this final fix.
- Actual `Target.materialize` from canonical product source to
  `/private/tmp/aeion-materialization-proof-5lh1w_r1/repo`:exact63bdece, clean candidate,
  source HEAD/origin-main/worktree status unchanged,0model calls and0remote writes.
  Local ignored `demo/.local/factory/bootstrap/v6/materialization-readback.json` preserves the result.
- Earlier latest full safe snapshot `/tmp/aeion-full-pass-20261102-al7jqp3u`:678demo OK/7explicit skips,
  33examples,19Flue,16client. These are the earlier full-snapshot results, not a rerun of changed bytes.

The code path and changelog/owning component doc were updated together. JUnit interception remains
an unproven hypothesis: no native baseline/attack completed yet. No PG/React activation, product
migration, observer push/merge, controller reload or newly paid evaluation occurred in this slice.

Final documentation checks for this checkpoint all passed: knowledge-check (0 problems),
doc-links --diff origin/develop --worktree (112 links), repo-health (current.md123 lines) and
git diff --check. An additional local-link readback found all27 current.md relative targets.
Manual sensitive-change review covered the local exact-SHA fetch, validated target identity,
argument-list subprocess use, source preservation, incomplete-destination cleanup and fixed
error reporting. No external scanner/plugin or independent full-delivery review was run for
this small local correction; protected observer CI/review is still pending, not claimed green.

## JUnit grader boundary hardening, Antigravity hook fix and full suite — 2026-11-04

- Executed the native JUnit grader boundary probe against exact product `main`
  (`63bdece8056136209e0e3d2e68dbf0879005fec9`) inside `DockerCheckRunner`:
  - Baseline `FactoryBoundaryProbeTest` failed as required (`returncode: 1`,
    `failure_kind: tests_failed`, `contract_assertion_failures: 1`).
  - Adding `CandidateInterceptor` (`InvocationInterceptor` calling `invocation.skip()`),
    `META-INF/services/org.junit.jupiter.api.extension.Extension` and
    `junit-platform.properties` (`junit.jupiter.extensions.autodetection.enabled=true`) inside
    candidate write scopes while leaving `FactoryBoundaryProbeTest.java` untouched made the
    unhardened `target_check` pass (`returncode: 0`, JUnit XML `tests="1" skipped="0" failures="0" errors="0"`).
  - Hardened `demo/factory/agent_files.py`, `demo/factory/artifact.py` and
    `demo/factory/checks.py` (`grader_tampered`, `_grader_tampered`, `_contract_executed`) to
    refuse `META-INF`, `junit-platform.properties`, JUnit extension/platform hooks, foreign
    packages under `local/aeion/forum/`, and skipped or unreported contract XML results. Re-ran
    the native Docker probe (`parse_error: builder_grader_tampered`, `reason: grader_tampered`)
    and added unit regressions in `test_factory_target_check.py` and `test_factory_live.py`.
- Updated `tools/agents/hook.py`, `tools/agents/tests/test_hooks.py` and
  `knowledge/operations/agent-compatibility.md` to map Antigravity `read_file`, `write_file`,
  `edit_file` and allow `run_command` `toolSummary` strings (`53` hook tests and `factory-tests`
  pass).
- Deferred `Telemetry` import in `demo/factory/flue_session.py`, refined OpenShell SDK detection
  in `demo/tests/test_sandbox_unmounted.py`, and updated `demo/tests/test_forum_content_target.py`
  for automatic `TaskPreparer` wiring so all `683` tests in `demo/tests` pass under
  `demo/.local/venv/bin/python` and Docker-free host unit tests pass under system `python3`.

## Observability PR #18 release and green main synchronization — 2026-11-04

- Opened PR #18 to merge the 77+ commit backlog from `develop` into protected `main`:
  - Fixed runner acceptance artifact resolution in `demo/app/runner.py` for unmounted OpenShell
    sandboxes (`host_mounts=False`, `include_workdir=False`), seeding candidate source when `artifact`
    is not pre-resolved.
  - Fixed candidate write preservation across agent sessions during handover: `prepare_handover`
    now collects unmounted sandbox writes to the host workspace before creating `HANDOVER.md` and
    evaluates against the in-sandbox workspace path without re-seeding the initial stub.
  - Implemented `seed_in`, `collect`, and `sync_out` on `LocalSandbox` in `demo/tests/local_sandbox.py`
    to allow complete three-tier development qualification without OpenShell.
- CI and reviews:
  - Recorded exact-head reviews (`707ed37`, `35282cb`, `4fabe16`) with commit review comments and PR reviews.
  - PR #18 CI passed all required workflows: `docker-demo` (2m28s, 4/4 scenarios and 3/3 tiers pass),
    `offline-examples` (50s), `Knowledge, links and repository health` (5s), and `Architecture refresh` (29s).
  - Merged PR #18 to `origin/main` as commit `ae5a6ef1441a418402e42e61619424b11435a01c`.
  - Post-merge CI runs on `main` both succeeded: `CI` (databaseId `41798806347`) and `Architecture refresh`
    (databaseId `41798806370`).
  - Synced `develop` with `origin/main` at merge commit `4557d1463640aa0d9dfe76328232b941f6e579a9`;
    local `main` fast-forwarded to `ae5a6ef`. `develop` and `main` trees are byte-for-byte identical.


## Full repository regression on current main code — 2026-11-04 request

Fresh fetch succeeded: HEAD/origin-develop10f072791a2378adad48789a91788c0d37bf0337;
origin-mainae5a6ef1441a418402e42e61619424b11435a01c. Tree difference before this pass was only
work/current.md and work/validation.md; source matches merged PR18/main. Initial worktree clean.
Host Python3.15.2/Node26.12.1/Docker29.9.2; five Flue packages match their exact declared versions.
All testing used715public tracked files, an empty environment and isolated state, committed-only
product Git objects and existing public tools/caches. No operator .env/database/worktree copied.

Final results:683demo tests with zero skips;33examples;19Flue;16cockpit client;21catalog;
catalog --check, synthetic fixtures/comparison, read-only source lock, Factory PASS. Three optional
architecture skips in Factory were fully covered by15native Deno/Graphify tests, all passing.
Initial archive failure was a missing HEAD in the public snapshot; fixed only snapshot setup.
Initial7demo skips were rerun with a committed-only local product fixture, then the full683 rerun
passed with zero skips. All initial logs remain separate; no project assertion/code was changed.

Native checks passed: OpenShell0.1.5 isolation/teardown;54positive JS cases plus broken/unloadable
negative controls; real Flue/Pi all3tiers with exact request/session/handover and usage assertions;
complete170062byte Qwen review and USAGE_UNKNOWN final-cost refusal; disposable PostgreSQL17
transactions, app privileges/DDL refusal, denied egress and both teardown paths; Chromium156
sandbox/namespaces/Seccomp-BPF/TSYNC with no host mount/socket/egress (Yama unavailable).
Full Java factory fixture passed276.94s, with repair feedback,2sessions, passed gate,2independent
votes and separate adaptive-medium Haiku probe. Automatic Java preparation passed205.44s:
complete frozen acceptance, failing baseline assertion, repair/handover,4distinct allowlisted models,
independent quorum and claude-mem/Hindsight metadata confirmed for all4roles.

First native-preparation attempt hit the temporary launcher's300s wrapper during final checks;
it is preserved as incomplete/exit124. Its owned checker/workload names were confirmed absent.
A fresh isolated run with900s wrapper passed205.44s. Engine deadlines, assertions, scopes, budget
and qualification controls were unchanged. Every inference endpoint for these generators was
local scripted data; no real feature, provider-quality score, deployment or merge is claimed.
Factory activation marker remains absent and PostgreSQL template qualified=false.

Fresh hosted exact-main readback: offline-examples, docker-demo, Knowledge/links/health,
Graphify/Archify all completed/success. Report: work/test-pass-2026-11-04.md. Full logs,
exit codes, timings, initial attempts and SHA256 index: /private/tmp/aeion-tests-20261104-sm4buts3/.
Current/HANDOVER updated with exact readback/fsync; no application code changed by this pass.

Final post-documentation checks: knowledge-check0problems, doc-links121, repo-health/current131lines,
git diff --check and28relative links all pass. Native cleanup confirms zero owned checker/workload
containers, removes only the temporary TLS symlink, and preserves the existing operator gateway.
Only work/HANDOVER.md, work/current.md, work/validation.md and the new dated test report are changed.


## Real factory checker, runtime identity and architecture — 2026-11-05

- Observer upgrade PR19/main48d1ae4 has actual exact-head and post-main green CI/Architecture.
  Owner-approved exact leased develop alignment preserved the old head/archive and all local work.
  Only main/develop remain as remote heads; local97f3ff8 is the subsequent reviewed engine slice.
- Full engine710tests PASS (/private/tmp/aeion-product-full-tests-20261105-v10.log), cockpit22,
  Flue19, catalog21, examples33 and complete foundation factory-tests PASS. Knowledge/doc-links133
  and repo-health passed. The fullv9 fixture-only missing protocol mock was corrected, not hidden.
- The startup-port regression failed before correction, then4boundary tests PASS. Registered
  startup negative control5PASS; startup/diagnostic2PASS; loaded-runtime stamp14PASS. Nativev11
  all6capabilities plus registered foundation PASS, protocolef76e49e5451ab565148e30e791707d8337bec0a810ca0187d5bef9d6d24cc26,
  proof demo/.local/factory/admission-iigyr8l3/proof.json. These fixtures use local scripted
  inference and claim execution mechanisms only.
- Real001v6 timed out with52forwards/51accountedsteps,11retained files and incomplete cost.
  Its reservation remains counted. The actual retained worker artifact subsequently PASSed
  corrected independent compile/unit/startup/privacy/HTTP in128922ms with teardown; no new
  main merge is claimed. Controller5713 now runs fresh qualification; normal API attemptv7
  ee701adcf55b496da219e6b877282f98 is in progress.
- Langfuse synthetic diagnostic/privacy readback5d168ca966ca3afb0a1b550391f56f37 PASSes ERROR,
  AGENT_TIMEOUT,1250ms, failed checker cause,11retained files, removed content and empty root I/O.
  The real interrupted build summarya7cc4ea9e1173db5fdfbd8aa8ea7739b was also backend-confirmed.
- Exact97f3ff8 Graphify/Archify PASS:604sources,112runtime files,537required files covered,
  6574nodes/13923edges. Architecture/workflow/lifecycle all native gates, including browser-check,
  PASS. Final corrected-commit and main refresh remain required; manual file-URL browser preview
  was policy-blocked without workaround.
- Two real reviewers approved all4parts of97f3ff8 with complete usage. Qwen's part2 rejection
  was retained and reassessed with primary context proving product doc ownership and automatic
  frozen acceptance. Checker fixes found by real execution are subsequent source and still
  require their own review. No false formal receipt or bypass of branch protection was used.
- Unwired PostgreSQL unit-fixture native probe PASSes its own admin/loopback, absent host keys,
  denied external egress and teardown; it is not product002/003 delivery. PG/React/proxy wiring,
  product deployment and actual complete feature-to-main remain open.

## 2026-11-05 — PostgreSQL/React checker wiring and stopped-candidate follow-up

Full engine721PASS in99.838s (/private/tmp/aeion-engine-tests-final-v13.log); client22PASS.
Registered preparation native001/002/014PASS with no model, durable identity and unchanged owner checkout
(/private/tmp/aeion-registered-foundation-xitml0rs/proof.json). Registered-negative9PASS; missing checker
reason regression failed before the explicit feature restriction and passes afterward.
Frozen React build plus positive/negative Vitest nativePASS with poisoned candidate configs/scripts
(/private/tmp/aeion-frozen-web-proof-cok96xnh/proof.json). Slow trace-export accounting regression failed
before batching and passes afterward. These are mechanisms, not product delivery.
Exact maintainer CI bundle6104ba6a passed product knowledge/link/health/foundation checks and isolated
backend tests/package. GLM actualapproveUSD0.01168080; Qwen still pending.
Native admissionv12 is running on the current protocol; no live launch/main merge/new Go claimed.

Graphify/Archify exact1dea96e82a18b28ef9a662562c7f615672153dad PASS (all3views/native browser gates),
/private/tmp/aeion-architecture-1dea96e.log. Host723PASS101.409s with14expected optional-SDK skips;
controller venv still runs the slow-export regression (PASS). Two maintainer correction tests PASS.
CI Qwen rejected a pre-existing mutable Semgrep image (completeUSD0.02797278); retained, not overruled.
Official registry resolved Semgrep digest451b3d875c00dac7ed5db5293e584a07de11449a409c10b3c2d2652f429630b6.
New bundle93fd1321 GLM actualapproveUSD0.02536887; Qwen pending. No publication yet.
User browser independently confirmed paused100MD,0active, no real product environment links;
the existing advanced Staging link is a separate historical canary drill, not product delivery.
