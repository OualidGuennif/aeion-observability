# Current work

Updated 2026-11-09. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Builder check diagnostics, signature streak and round continuation — ACTIVE

- Owner decision: make live builders see structured JUnit failure diagnostics, stop only on repeated identical failure signatures after baseline reproduction, use correction rounds on `repeated_check_failure`, and seed the cleanest validated candidate on a relaunch of the same base and spec.
- State: `_junit_failures` enriches `failed_tests` from JUnit XML, `note_check_failure` tracks `(reason, failed_tests, compiler_errors)` with a 5-check streak after skipping untouched baseline reproduction, `next_step` advances through correction rounds on `repeated_check_failure`, `prior_candidate` seeds the cleanest validated candidate on same-base/same-spec relaunch, Feature 001 instructions explain Quarkus config ordinals, and `demo/forum/features/TEMPLATE.md` provides the canonical 8-section feature contract template alongside the 100 validated specs. VERSION stays 1.9.0.
- Next: merge the reviewed develop PR to main, resync develop, and requalify/reload the live controller before the next Feature 001 launch (who: agent, then owner launch).
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
