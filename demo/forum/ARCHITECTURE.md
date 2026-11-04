# Agora — product architecture

Decision: **quarkus-postgresql-react-web-v1**, approved by the owner on 2026-11-03.
This is the target contract. The running product still uses SQLite and an Expo browser client;
the migration and replacement are not completed by this document.

## Intent

One browser web application: React/TypeScript frontend, Quarkus/Java API and PostgreSQL product
database. Retain working backend behavior and tests. PostgreSQL provides the shared transactional
store and full-text search required by the catalog; this choice does not by itself guarantee
security or reliability. Native mobile delivery is deferred.

## Data sources

- Canonical definitions: `tools/specs_a.py` through `specs_f.py`; generated contracts: `features/`.
- Separate product repository: `OualidGuennif/aeion-autonomous-forum`. Paths below are relative
  to that repository, not an instruction to create product sources in Observability.
- Inspected baseline: `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`, Quarkus 3.40.1, Java 25,
  Gradle build, SQLite JDBC/Hibernate and Expo/React Native browser client. These describe the
  existing checkout, not an instruction to upgrade dependencies.
- Official documentation, inspected 2026-11-03: [Quarkus data sources](https://quarkus.io/guides/datasource/),
  [Quarkus Flyway](https://quarkus.io/guides/flyway/) and [React build tools](https://react.dev/learn/build-a-react-app-from-scratch).
  Quarkus documents PostgreSQL JDBC and Flyway integration. React documents Vite as one build-tool
  option; choosing a static client here is an Æion decision, not React's universal recommendation.

## Inputs

| Product path | Responsibility |
| --- | --- |
| `demo/forum-app/` | Existing Quarkus API, Java sources, JUnit tests, build and product service configuration |
| `demo/forum-app/src/main/resources/db/migration/` | Versioned PostgreSQL schema and migrations |
| `demo/forum-app/src/main/resources/rules/` | Reviewed immutable rule versions |
| `demo/forum-app/src/main/resources/personas/` | Reviewed typed persona data |
| `demo/forum-app/src/main/resources/corpus/items/` | Synthetic offline corpus |
| `demo/forum-app/src/test/resources/` | Disposable product fixtures |
| `demo/forum-web/` | React DOM/TypeScript browser client, local assets, frontend and browser tests |
| `demo/forum-docs/` | Product operating notes and feature reports |

Keep existing Quarkus/JAX-RS, Jackson and Jakarta validation conventions. Use the Quarkus-managed
PostgreSQL JDBC driver and one Flyway migration history; remove the custom SQLite runner only
after equivalence tests. Keep Hibernate schema generation disabled outside disposable tests.
Use the current Gradle build; Java tests use JUnit/Quarkus and a real disposable PostgreSQL
instance, never SQLite/H2 compatibility as evidence of PostgreSQL correctness.

React uses browser DOM elements, a small Vite build and a pinned npm lock. Reuse existing API
interfaces where correct; keep routing and data loading simple. No Expo, React Native,
Capacitor, Next.js server or new frontend backend. The production client and API share one
origin, with relative API URLs; a development proxy must not become a production wildcard
CORS policy. No secret belongs in a browser build variable, localStorage or telemetry.

## Outputs

- Feature 002 owns a tested SQLite-to-PostgreSQL cutover, backup/restore proof, schema validation
  and explicit rollback. Never delete or mutate the old volume as part of bootstrap.
- Feature 003 owns the PostgreSQL test harness. Feature 014 owns the React web shell and removal
  of active mobile build/runtime paths. Existing mobile sources may be retired in that reviewed
  product change; do not maintain two clients.
- All other features extend this architecture. Freeze spec, architecture, source and acceptance
  identities for each attempt. Old SQLite/Expo receipts stay historical and cannot certify the
  PostgreSQL/React contract. A changed requirement needs requalification, not a synthetic merge.
- A missing protected test, stale base, unsafe migration, missing budget or permission remains
  an explicit hold. Automatic preparation may propose tests; it cannot approve its own evidence.

## Invariants

1. The product has one database engine and one active browser client after cutover. Features
   002/003/014 and their protected integration checks prove it.
2. Browser code has no authority over authentication, object visibility, quotas or moderation.
   Every mutation is authorized and validated by Quarkus; 005/006/017/043/063 test refusals.
3. Product builders cannot write observer `demo/app/`, `demo/flue/`, `demo/factory/`, protected
   contracts, repository policy, credentials or CI. Catalog scope tests reject these paths.
4. A database transition preserves data and audit integrity. Feature 002 must compare row counts,
   stable IDs, timestamps, normalized content and audit verification after export/import and
   after a disposable restore; loss or mismatch blocks cutover.
5. Accessible React UI includes labels, focus handling, loading/empty/error/retry states and
   keyboard operation. Features 018/040/099 prove browser behavior with JavaScript enabled.

## Determinism

Quarkus owns transactions, authorization, validation, identity and policy. React displays
server state and may perform advisory input validation only. Use UTC instants in storage,
Europe/Paris for business-day/week boundaries, frozen clocks and explicit sort tie-breaks.
JSON DTOs and problem codes are stable interfaces. Hostile Markdown and model output remain
data. Sanitizer-produced HTML has one reviewed React rendering boundary; all other text uses
normal escaped JSX. CSP disallows inline script by default; a nonce is needed only if an actual
reviewed inline script exists. Do not add SSR solely to satisfy superseded template specs.

## Acceptance checks

```sh
python3 -B demo/forum/tools/generate_features.py --check
python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
```

These check the catalog, not the migration or webapp. Product readiness additionally requires
the protected PostgreSQL migration/restore and Java suites, frontend type/build checks and
real browser/API refusal scenarios. Pin tool/image versions before those runs; do not invent
passing commands for a web package that has not been created yet.

## Out of scope

- Native mobile apps, a second backend, additional databases or a frontend server framework.
- Migrating the factory's own SQLite ledger or the observability backend databases.
- Adding Kafka, Redis, Kubernetes or a new gateway merely for this stack change. Existing optional
  Kafka behavior remains optional; PostgreSQL transactions/outbox suffice for the current scope.
- Deployment, dropping old data, or treating these specs as runtime qualification.
