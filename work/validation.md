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
