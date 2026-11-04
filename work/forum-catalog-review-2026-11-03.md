# Review of all 100 Agora contracts — 2026-11-03

Owner-approved decision: keep Quarkus/Java/Gradle, move product storage to PostgreSQL and
replace the active Expo/React Native client with React DOM/TypeScript web. No native mobile
application is planned in this catalog revision. This report is a source/contract review,
not evidence that those product transitions have been implemented or deployed.

All six canonical definition files were inspected, including goals, scopes, acceptance,
security, tests and exclusions for every ID. Every feature now has three feature-specific
implementation steps. Existing IDs are preserved; a separate deterministic `sequence` puts
every dependency before its consumer, then orders ready items by phase and stable ID. The
cockpit renders that sequence without changing server admission authority.

## Results

- Exactly 100 generated MDs; eight contract sections per MD; no missing or duplicate ID.
- 354–637 words per MD; median 397 words. Feature 002 is the longest and remains honestly size L:
  a data migration needs backup/import/restore evidence. Other work is size S/M; integration
  recipes reuse existing prerequisites instead of implementing missing subsystems internally.
- 342 dependency edges, acyclic and phase-compatible. Repaired prerequisites include comment
  voting/permalinks, upheld violations, quota normalization, reply attribution, corpus citation,
  interest scheduling, first-page metrics and accessibility coverage.
- Literal scopes refer only to product app/web/docs roots in the separate product repository.
  077/082/086 remain disjoint parallel candidates. Factory/harness/credentials are excluded.
- The architecture content digest is embedded in every MD and manifest feature, so a shared
  architecture change changes the frozen catalog/spec identity after regeneration.
- Removed contradictory FastAPI/pytest/server-template/no-JavaScript requirements. Added a
  React-compatible CSRF path and production CSP without an unnecessary inline-script requirement.
- Fixed appeal/visibility, comment-provenance, override-audit-content, breaker-recovery and
  small-cohort disclosure contradictions. Memory remains advisory; deterministic authority,
  independent protected checks, review identity and unknown usage stay explicit.

## Per-feature assessment

Every row also receives the shared architecture, bounded steps, literal product scopes and
protected acceptance contract. Retained behavior was kept intentionally rather than rewritten
for novelty.

| Stable ID | Sequence | Review decision / correction |
| --- | --- | --- |
| 001 | 001 | Replace FastAPI with the existing Quarkus configuration/liveness contract. |
| 002 | 002 | Preserve SQLite data; add PostgreSQL migration, import, restore and explicit cutover proof. |
| 003 | 003 | Replace pytest with JUnit/Quarkus and real disposable PostgreSQL isolation. |
| 004 | 004 | Keep pinned Argon2id and server-derived disabled-account behavior. |
| 005 | 005 | Keep opaque HttpOnly sessions, rotation and bounded expiry. |
| 006 | 006 | Resolve agent-exemption contradiction and supply the React CSRF bootstrap path. |
| 007 | 007 | Keep one normalized Markdown representation, inert HTML and explicit size refusals. |
| 008 | 008 | Keep atomic PostgreSQL admission; performance remains baseline-specific. |
| 009 | 009 | Fix contradictory audit grants using a restricted append function; state hash-chain limits. |
| 010 | 010 | Keep fixed-code problem JSON without copying exception or request content. |
| 011 | 011 | Keep allowlisted configuration and minimal child environments; no secret inspection. |
| 012 | 012 | Keep all-surface canaries and real readback; collector presence is insufficient. |
| 013 | 013 | Use React production CSP; do not invent an inline script merely to need a nonce. |
| 014 | 014 | Replace server templates and Expo with one React DOM browser shell. |
| 015 | 015 | Keep database readiness separate from liveness and telemetry degradation. |
| 016 | 016 | Reuse Quarkus shutdown; declare the pool/database prerequisite. |
| 017 | 017 | Replace Python validation terminology with strict Jackson/Jakarta and bounded stream handling. |
| 018 | 018 | Replace no-JavaScript requirements with accessible keyboard and dynamic React states. |
| 019 | 021 | Keep channels tied to immutable rules and audited privileged commands. |
| 020 | 022 | Keep membership/object filtering on every read and write surface. |
| 021 | 023 | Rename misleading composer feature: held storage and safe reads only. |
| 022 | 024 | Keep held comment storage, visible ancestry and depth-three refusal. |
| 023 | 035 | Add the missing comment-storage dependency for comment votes. |
| 024 | 036 | Keep pure ranking, frozen time and stable ties; no learned ranking. |
| 025 | 025 | Reuse PostgreSQL French search, bound terms and filter visibility before snippets. |
| 026 | 038 | Keep reader-bound frozen snapshots; insertion cannot corrupt an existing cursor. |
| 027 | 026 | Keep controlled tags and the three-tag cap, not an editable taxonomy. |
| 028 | 027 | Keep deduplicated notifications with visibility rechecks after creation. |
| 029 | 028 | Keep external URLs inert and never reachable as workload fetch destinations. |
| 030 | 029 | Keep edits pending until readmitted; preserve revisions and tombstones. |
| 031 | 041 | Keep server-derived provenance consistent across all React read surfaces. |
| 032 | 030 | Keep numeric shingle evidence; do not claim semantic paraphrase detection. |
| 033 | 037 | Keep stable overflow deferral; all eligible snapshot IDs remain reachable. |
| 034 | 039 | Keep measured index budgets and load-bearing negative cases. |
| 035 | 042 | Replace unreliable whole-text credential grep with schema-path exclusion tests. |
| 036 | 031 | Keep immutable rule/version citations with current channel access. |
| 037 | 032 | Add the missing comments dependency; retain canonical browser deep links. |
| 038 | 033 | Remove redundant bearer unsubscribe authority; use session plus CSRF. |
| 039 | 043 | Keep reproducible disposable fixtures and production-target refusal, even with force. |
| 040 | 044 | Require actual PostgreSQL/Quarkus/React browser integration; retain three control mutations. |
| 041 | 019 | Use actual Java resource paths and one retained rules source. |
| 042 | 045 | Bound to one pure reviewed rules function; no model, storage or moderation subsystem. |
| 043 | 020 | Name Java/JAX-RS route coverage and explicit public read declarations. |
| 044 | 046 | Keep server-derived reporter and unique open reporter/target identity. |
| 045 | 047 | Keep pure queue priority with frozen aging and stable ties. |
| 046 | 048 | Keep transaction-coupled audit and current deterministic recomputation. |
| 047 | 049 | Prevent appeal restoration from bypassing changed current rules. |
| 048 | 050 | Clarify the separately authorized exception for permanent sanctions. |
| 049 | 051 | Add actual decision/appeal prerequisites for upheld-violation counts. |
| 050 | 072 | Reuse the qualified three-tool moderator; do not build another runtime. |
| 051 | 052 | Keep free-text override justification in private storage, outside metadata-only audit. |
| 052 | 053 | Bound deterministic excerpt filtering; unknown injections still cannot gain authority. |
| 053 | 054 | Align audit rights with the restricted append-function contract. |
| 054 | 055 | Keep tuning/held-out synthetic labels and explicit quality denominators. |
| 055 | 056 | Keep named bypass regressions, without a universal safety claim. |
| 056 | 057 | Keep explicit hold/recovery; turning off a switch does not publish held history. |
| 057 | 058 | Keep reviewed rule diffs and cited-code retention; fixtures do not grant approval. |
| 058 | 059 | Prevent reconstructing suppressed counts through complementary public totals. |
| 059 | 034 | Keep credentials at the trusted broker, with immediate revocation. |
| 060 | 040 | Use actual persona resource paths and freeze typed metadata per run. |
| 061 | 061 | Add normalization dependency and resolve quota/normalization ordering and replay conflict. |
| 062 | 073 | Keep claimed scheduled slots, quiet hours and restart reconciliation. |
| 063 | 074 | Bound to integration of existing guards; distinguish action schemas and route quotas. |
| 064 | 062 | Remove premature scheduler integration from this advisory-only acceptance contract. |
| 065 | 063 | Add persona and visibility prerequisites; keep metadata-only reply policy. |
| 066 | 064 | Keep distinct broker tool sets and real OS refusal evidence; tool lists alone are insufficient. |
| 067 | 065 | Keep deduplicated cross-author signals without changing moderation visibility. |
| 068 | 066 | Keep reader-visible counts only and no private persona or channel leakage. |
| 069 | 067 | Keep bounded identifiers/codes-only claude-mem checkpoints and safe missing-memory behavior. |
| 070 | 068 | Remove contradictory body-reading statement; require closure/lock prerequisite. |
| 071 | 069 | Use one leased half-open probe after cooldown, not a simultaneous retry burst. |
| 072 | 070 | Fix incorrect inherited comment provenance; bind each reply to its own author/persona. |
| 073 | 071 | Keep final run-ID metadata counts and honest pending/unknown trace receipts. |
| 074 | 076 | Compose already-tested services; add the read-only smoke prerequisite. |
| 075 | 077 | Declare sanitizer/link prerequisites for the promised inert text contract. |
| 076 | 078 | Keep local confined idempotent loading and actual egress refusal tests. |
| 077 | 079 | Keep 200 synthetic French items; narrow data/doc scopes remain parallel-safe. |
| 078 | 080 | Specify Europe/Paris day boundaries and exactly-once logical selection counting. |
| 079 | 082 | Require actual corpus data/citation prerequisites and count committed visible threads only. |
| 080 | 081 | Add the loader prerequisite for persisted corpus references and fallback rendering. |
| 081 | 083 | Keep atomic rename plus descriptor-based confined reads; checksums alone are insufficient. |
| 082 | 084 | Keep this documentation-only; no real-source loader or runtime switch. |
| 083 | 085 | Never override zero persona weights to fake category coverage; report degraded inputs. |
| 084 | 086 | Add interest/scheduler dependencies and remove ambiguous invitation retry semantics. |
| 085 | 087 | Add duplicate-evidence and pagination dependencies for first-page metrics. |
| 086 | 088 | Replace Python test path with one JUnit class and isolated corpus fixtures. |
| 087 | 089 | Generate fixed React SVG nodes; no arbitrary HTML/SVG string injection sink. |
| 088 | 090 | Keep audited bounded pins and transactional cap/expiry behavior. |
| 089 | 091 | Use one channel/Europe-Paris-week key and normal admission, including private-data exclusion. |
| 090 | 092 | Keep current source/destination visibility and approval for retained deleted-source excerpts. |
| 091 | 093 | Promise private API isolation, not impossible prevention of all behavioral inference. |
| 092 | 094 | Keep public edit counts separate from moderator-only revision content. |
| 093 | 095 | Pin activity windows/cache and reuse complementary suppression in JSON and React. |
| 094 | 096 | Use Intl/React text helpers; never rewrite normalized storage, code or HTML attributes. |
| 095 | 075 | Add problem-response prerequisite and prevent automatic replay of uncertain mutations. |
| 096 | 060 | Keep slow/lock predicates, atomic audit and later full-route integration. |
| 097 | 097 | Keep allowlisted immutable exports; credential paths differ from valid audit hashes. |
| 098 | 098 | Keep fixed resource/fixture/latency evidence and all repetitions, not a universal SLA. |
| 099 | 100 | Audit the actual React product and declare dependencies for the views it checks. |
| 100 | 099 | Keep retained versioned guidelines and integrate the synthetic-source note. |

## Sources and verification limits

The existing product baseline inspected is `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`:
Quarkus 3.40.1, Java 25, SQLite JDBC/Hibernate and the Expo browser client. Product files were
read only. No credential, transcript, database row or raw environment was inspected. No model
call, GitHub write, deployment, database migration or data-volume deletion was performed for
this catalog revision.

Official documentation inspected 2026-11-03: [Quarkus data sources](https://quarkus.io/guides/datasource/),
[Quarkus Flyway](https://quarkus.io/guides/flyway/), [React build tools](https://react.dev/learn/build-a-react-app-from-scratch).
The choice of a static Vite client beside the existing API is project-specific. PostgreSQL's
selection satisfies shared transactions/search and the owner decision; it is not itself proof
of stronger security or successful operation.

Catalog tests, runtime manifest tests, client tests and document checks are recorded in
`work/validation.md`. They do not qualify PostgreSQL/React runtime behavior. Previously pinned
007/013/017 targets describe the earlier product base and cannot certify changed contracts.
The replacement Flue factory remains held until its actual current path is qualified.
