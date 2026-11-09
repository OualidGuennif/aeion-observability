# Current work

Updated 2026-11-09. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Out-of-scope Spec doc guard and review fixes — ACTIVE

- Owner decision: stop the Feature 001 rule-L3 failure loop by refusing and reverting code edits whose Spec document is outside write scopes, apply the observability review fixes (F1–F4, G1), and ship through develop to main.
- State: `flue_builder.py` and `dispatch.py` refuse and revert out-of-scope Spec edits (`knowledge_doc_outside_scope`), `Telemetry.emit` uses a non-blocking log queue, `flue-factory-routing-v6` binds the treatment digest, lab autonomy requires explicit zero intervention, and two-decimal budget formatting is enforced. Feature 001 build 39db9530e56d stays held (`owner_review_required`) until the new code is merged and the live controller is reloaded. VERSION stays 1.9.0.
- Next: merge the reviewed develop PR to main, resync develop, and reload/requalify the live controller before any new Feature 001 launch (who: agent, then owner launch).
- Blocker: product pull requests 7 through 11 stay open and unmerged; features 002, 003 and 013 stay `catalog_changed` until 001 integrates on main.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

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
