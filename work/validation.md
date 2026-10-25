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
