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
