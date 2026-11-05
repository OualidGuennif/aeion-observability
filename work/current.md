# Current work

Updated 2026-11-05. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Secure factory delivery — ACTIVE

- Owner decision: finish MD→Flue/Pi/OpenShell tier3→external acceptance→two independent reviewer families→PR/exact-head CI→confirmed main, with Quarkus/PostgreSQL/React, preserved data and15USD/day per repository.
- State: main 3455063 (PR22, CI/Architecture green) has the typed-verdict hook, failed-review retry, relay 300s bound, `demo/budget.conf`, simplified cockpit and gRPC fork fix. PR23 (draft self-test label) merged as main 3613608; develop resynced locally (985260b, unpushed). Controller live as PID91475. In progress (uncommitted): dark mode for cockpit and lab (demo/app/theme.css/js), lab showcase rebuild with functional memory room.
- Next: owner visual yes (checks and docs done), then review, push, PR, merge on green CI (who: agent; owner visual yes).
- Blocker: no product feature has completed the whole circuit. Product deployment and002/014 remain open. No false all-green claim.
- Evidence: [Delivery report](factory-delivery-2026-11-05.md); [execution contract](../knowledge/components/factory-flue.md); https://github.com/OualidGuennif/aeion-observability/pull/20 .

## Real001 and reviewer context — ACTIVE

- Owner decision: investigate actual failure paths, preserve failures/costs, require two real independent votes and never hand-edit product business source.
- State: the owner cancelled v8 and relaunched 001 as 51b7fc97c57744f8a07aa2f197cd8fb8 on the live controller (preparing at 2026-11-05 evening). Earlier: v8 fe0e69f0013248558a8dbc9961c0e30a held at generation2. The one-time failed-review retry reran the external gate (PASS), then DeepSeek hit the relay's fixed45s socket bound (TRANSPORT_ERROR, zero tokens, trace d52dbac0). Earlier: Qwen approved after the v2 context; DeepSeek previously ended without a typed verdict; the original Qwen v1 scope rejection is archived. Author GLM retained13files, known0.16105089USD.
- Latest: 51b7fc97 failed after 33 min: author AGENT_TIMEOUT with its self-test still at explicit_database_less_startup_rejected; the gate confirmed product_unit_tests_failed (DatabaseLessBootTest.databaseWorkReportsItsRefusalInsteadOfFailing); known author cost 0.25635032USD. No review spent.
- Latest: 3bb1d4cd was revoked mid-build (ATTEMPT_REVOKED, 0.09355716USD) because an agent edit to protocol-hashed demo/app/memory.py broke admission; the file is restored and admission is ready again.
- Next: owner relaunches 001 from the cockpit; agent follows it to gate, two reviews, product PR, CI and main (who: owner launch, agent watches).
- Blocker: no review override, second vote or product publication. Unknown v6 usage retains0.50USD reservation; v7 known0.11236812USD failed and remains historical. Forum counted1.04USD, Observer1.52USD, separate daily15USD purses.
- Evidence: artifact26cb980e8e1d98deb19b26c3c13d70bef1048d0e19b0ef161ca1493fedb658ca; base e55b820ca4534738283df1674ba80be43ec03fa5. Author trace f0d45197e8061d0120571df6b259f6b2; Qwen301d9f7cdc7ce2877e3fb9dfbc8cd0f4. No active actual job now.

## Trusted product CI and PostgreSQL/React — PARTIAL

- Owner decision: workers may propose dependency transitions without changing their evaluator; trusted CI updates use separate publisher/release credential roles.
- State: product CI PR5 genuinely merged as e55b820ca4534738283df1674ba80be43ec03fa5, all6exact-head checks and post-main CI/architecture PASS. Corrected9-file bundle93fd1321 has two actual approvals; old Semgrep rejection retained. Main contains pinned scanner/PG17 CI and fixed React check programs. Observer adapters001/002/014, isolated unit PG, migration/import/restore and frozen React build/test are implemented and natively qualified.
- Next: implement product014React and002PostgreSQL through actual workers after001 integration (who: agent).
- Blocker: qualified adapters and CI are not implemented product migrations or deployed React. Preserve canonical checkout HEADa50d607 and untracked local artifacts/data. No operator database migrated/deleted.
- Evidence: https://github.com/OualidGuennif/aeion-autonomous-forum/pull/5 ; [maintainer tool](product-ci-adapters-2026-11-05/maintain.py).

## Qualification, independent review and telemetry — VERIFIED BASE

- Owner decision: publish only exact reviewed source, keep metadata-only diagnostics and source-backed graphs.
- State: native v16 PASS (budget.conf bounds, relay300s idle, typed verdict hook), protocole7b346ef4041ea31080b68b6e2a01c8b570438ef0771819e7c69fbeeefade223, proof demo/.local/factory/admission-e2hb4h7b/proof.json, controller PID77547 restarted with `AEION_FACTORY_EXECUTION=live` and no active build. Full demo742 PASS. Same-chantier review consent remains valid within the total3USD ceiling.
- Next: qualify any protocol correction before controller reload; fresh diagnostics readback and final docs/checks/review/publish after correction (who: agent).
- Blocker: source edits intentionally revoke admission until native qualification/reload. Collector latest recovered-candidate metadata allowlist still needs safe collector-only reload. No zero-loss telemetry claim.
- Evidence: /private/tmp/aeion-engine-tests-final-v13.log; /private/tmp/aeion-host-tests-final.log; .aeion/reviews/138c6336aecc4f3825aa7e3a9b7a3241bf823649.md; main9c CI/Architecture green.

## Actual environments and cockpit links — OPEN

- Owner decision: provide real staging/production links and readable implementation stages; technical-only features may explicitly have no dedicated demo.
- State: tested product cookie-filtering proxy exists but is not wired. The old advanced Staging57101 link is a historical read-only canary drill, not the real forum. Existing forum container127.0.0.1:8081 uses owner untracked compose files and SQLite data; preserve it. Factory2.0.3 and pinned Langfuse4.75.0 are deployed with preserved backups/data.
- Next: wire actual checked product artifacts to isolated environments, prove readiness and exact source identity, then expose only verified links (who: agent).
- Blocker: no real staging/production deployment receipt/link yet. The cockpit now shows both as "Not deployed yet" and no longer shows the synthetic drill (owner visual yes pending). Do not relabel the existing unverified container as delivered main.
- Evidence: [Cockpit contract](../knowledge/components/operator-cockpit.md); [product proxy](../demo/factory/product_proxy.py); latest browser inspection confirmed the misleading advanced drill and missing prod link.
