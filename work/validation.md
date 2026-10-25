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
on `task/langfuse-opencode-demo`; no publication or production deployment is claimed.

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
Hosted CI has not run for this local branch; its new Docker job uses fake inference only.
