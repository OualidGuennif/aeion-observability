---
type: Component
title: "Flue factory execution"
description: "Deterministic supervision of untrusted Flue/Pi workers, isolated tools and protected publication."
status: draft
verified:
  - at: 2026-11-07
    what: "unittest correction rounds, connectivity, review circuit, artifact and recovery: a working CLI_FAILED resumes the same model; a quiet stop still crashes"
  - at: 2026-11-07
    what: "unittest budget, TLS, workspace and review retry: ceilings stay 150/50/1; summary splits settled and reserved; an unforwarded claim settles at zero; an incomplete forward stays reserved; one failed review retries once"
  - at: 2026-11-07
    what: "unittest CI correction: a comma in a required check name is kept; a known check adds one fixed repair sentence; a placeholder name is replaced once and that same correction is queued"
sources:
  - resource: ../../demo/factory/review_context.py
    title: "One-time operator repair of the old review envelope"
  - resource: ../../demo/factory/product_unit.py
    title: "Separate candidate unit-test database"
  - resource: ../../demo/factory/product_postgres.py
    title: "Fixed migration, import and restore oracles"
  - resource: ../../demo/factory/product_web.py
    title: "Frozen offline React runner"
  - resource: ../../demo/factory/product_proxy.py
    title: "Product cookie boundary, deployment not yet wired"
  - resource: ../../demo/factory/checker-tools/build-web.mjs
    title: "Fixed TypeScript and production build"
  - resource: ../../demo/factory/checker-tools/vitest.config.mjs
    title: "Fixed Vitest configuration"
  - resource: ../../demo/factory/checker-tools/tsconfig.web.json
    title: "Fixed frontend transform configuration"
  - resource: ../../work/product-ci-adapters-2026-11-05/maintain.py
    title: "Exact maintainer-only CI update"
  - resource: ../../work/product-ci-adapters-2026-11-05/ci.yml
    title: "PostgreSQL and React CI inputs"
  - resource: ../../demo/factory/dispatch.py
    title: "Factory supervisor, routing and publication"
  - resource: ../../demo/factory/connectivity.py
    title: "Same-model resume after a working CLI stop"
  - resource: ../../demo/factory/retention.py
    title: "Workspace and failed-branch retention"
  - resource: ../../demo/flue/src/context.ts
    title: "Shared factory agent context and feedback rule"
  - resource: ../../demo/flue/src/tools/submit-feedback.ts
    title: "Author owner-only feedback tool"
  - resource: ../../demo/factory/product_checks.py
    title: "Protected production and acceptance boundary"
  - resource: ../../demo/factory/flue_qualification.py
    title: "Exact current-protocol admission"
  - resource: ../../demo/app/sandbox.py
    title: "OpenShell boundary"
  - resource: ../../demo/app/bridge.py
    title: "Capability-scoped tool bridge"
  - resource: ../../demo/flue/src/agents/coder.ts
    title: "Pinned harness and metadata observer"
  - resource: ../../work/product-ci-bootstrap-2026-11-03/ci.yml
    title: "Merged trusted product CI bootstrap"
  - resource: ../../demo/factory/agent_files.py
    title: "Agent files"
  - resource: ../../demo/factory/bootstrap.py
    title: "Bootstrap"
  - resource: ../../demo/factory/github.py
    title: "Github"
  - resource: ../../demo/factory/budget.py
    title: "Daily purses, settled spend and open reservations"
  - resource: ../../demo/factory/inference_config.py
    title: "Inference config"
  - resource: ../../demo/factory/postgres.py
    title: "Postgres"
  - resource: ../../demo/factory/preparation.py
    title: "Preparation"
  - resource: ../../demo/factory/publication.py
    title: "Publication"
  - resource: ../../demo/factory/routing.py
    title: "Routing"
  - resource: ../../demo/factory/source.py
    title: "Source"
  - resource: ../../demo/flue/src/agents/preparer.ts
    title: "Preparer"
  - resource: ../../demo/flue/src/tools/submit-preparation.ts
    title: "Submit preparation"
---

# Flue factory execution

## Intent

Build selected product features with Flue/Pi and tier-3 OpenShell tools, then deterministically
validate, review, publish and confirm the result on main. LLM output and recalled memory never
hold authority. A successful cycle is a confirmed merge, not a generated file or opened PR.

## Data sources

Pinned product/target/contract and harness/image identities define the execution. Trusted
supervisor receipts define comparable model outcomes. Langfuse, claude-mem and Hindsight store
bounded metadata/checkpoints; recalled text is advisory and cannot edit policy or scores.

## Inputs

A maintainer bootstrap may deterministically import an already committed backend snapshot onto
the frozen empty-template main base. Its author is a byte-preserving import, not an invented
model identity. Two different eligible Flue models review all published bytes. The exception
admits only exact hashed CI/component/changelog/task documents owned by the supervisor; ordinary
worker/publication scopes still forbid policy files. The actual isolated backend checks, immutable
source identity, two complete real votes and current lease must pass before any remote write
(test_factory_bootstrap). This does not certify the new100-feature PostgreSQL/React contracts.
An expired bootstrap lease is never extended to keep spending. Only an exact unchanged bundle
with all prior costs known/settled, a completed first approval, an unforwarded failed second vote
and no publication job may carry that approval to a fresh attempt. The old attempt is fenced and
retained; an unknown cost or remote effect refuses this recovery (test_factory_bootstrap).
Worker completion and publication staging also verify the unexpired worker lease in their own
SQLite transaction. A still-dispatched stale process cannot enqueue a future remote effect or
complete the feature while waiting for restart reconciliation (test_factory_publication_state,
test_factory_recovery).
A known tree-creation403 can be explicitly rearmed after the owner fixes the publisher's
permissions. The two existing approvals/checks remain bound to the unchanged request; isolated
publisher reads must confirm the original main and absence of the attempt's branch and PR.
Unknown effects, changed payload, cancellation or an active lease refuse rearming. This local
retry starts no model and changes no remote ref (test_factory_publication_state,test_factory_bootstrap).

Before freezing a live task, a short-lived source synchronizer loads only the build read key.
It fetches the fixed product main into a unique temporary Git ref, checks ancestry and atomically
updates `refs/remotes/origin/main` against its previous SHA. No checkout/reset/stash or remote
write occurs; local HEAD and dirty/untracked files remain intact. Concurrent ref changes or a
rewritten remote main hold before any model reservation. Fetch diagnostics and credentials never
enter receipts; parent inference/publication keys are absent from the child environment. The
source module participates in the activation protocol hash (test_factory_source_sync,
test_factory_preparation). Git's [fetch](https://git-scm.com/docs/git-fetch) and
[conditional ref update](https://git-scm.com/docs/git-update-ref) define these operations.
Materialization also supports shallow source checkouts whose frozen main exists only in a
remote-tracking ref: if the fresh clone lacks that commit, fetch its exact SHA from the local
source without updating a branch or FETCH_HEAD. A failed fetch removes only the incomplete
clone and reports a fixed error, never private Git diagnostics; the source HEAD and operator
edits remain unchanged (test_factory_target).

Authenticated CSRF-protected feature selection; a validated tier-3 target; a qualified model
from the explicit six-model whitelist; operator-configured inference, publisher and release
roles in separate processes. No agent receives host credentials, source paths or authority
to select a repository, expand scopes, change tests, change budget or merge.

Automatic preparation freezes the complete catalog MD, approved architecture, committed product
base and narrower literal scopes before implementation. A tier-1 Flue preparer proposes a bounded
external Node acceptance, never a command or policy; the historical Java profile retains JUnit.
The exact registered001/002/014 MDs and architecture use fixed supervisor acceptance with no model request or
cost. A changed MD cannot reuse that oracle. Its untouched-baseline startup rejection is a
registered negative; arbitrary compiler/toolchain failure never qualifies an acceptance contract.
Ordinary contracts require actual failing external assertions on the untouched baseline.
The registered002/014 untouched baseline must lack their operator/browser source; compiler failure
or a missing checker reason cannot stand in for that absence. Positive candidates still need the
full migration/import/restore or production browser checks. These adapters do not implement the product.

Generated MDs begin with YAML frontmatter (`---`). The launcher binds the entire message as
`--message=<value>` so the CLI cannot parse that prefix as another option. This was reproduced
with the real CLI and a local scripted endpoint: before correction no request reached the
endpoint; after correction the unchanged MD reached it once. The native automatic-preparation
fixture now begins with frontmatter and exercises all role/acceptance/review paths.

Database-less startup probes run before the main app binds their shared owned loopback port.
Otherwise a refusal probe can read the already running app and report a false failure. Numeric
fixture values require unambiguous matching so thread numbers do not masquerade as disclosure.
The registered001 baseline accepts only its known database-less startup rejection or actual
failed external assertions; arbitrary compiler failure remains invalid negative evidence.
Loaded runtime identity is captured separately from the current disk proof. Requalifying changed
source cannot authorize stale Python objects: that process needs a clean reload. Same-source
freshness recovery preserves unstarted queued attempts. Routingv4 excludes outcomes collected
by the former colliding startup checker without deleting those historical rows.
The last fixed checker status/reason/digest survives later agent events and an interrupted role.
Its retained-file count is evidence, not approval to publish partial work or settle unknown usage.

The PostgreSQL check boundary uses a new disposable PostgreSQL 17 container per check, network
`none`, RAM-only data, no host paths or published ports. A non-root checker joins only that
container's network namespace; localhost reaches the disposable database, external routes stay
absent. Test credentials apply only to this disposable instance. Both containers are removed
and absence is confirmed on success, timeout or failure. This boundary alone does not qualify
the migration/restore contract or React adapter (test_factory_postgres, qualify_postgres.py).
Schema2 admission qualifies native execution capabilities: Flue/OpenShell, external acceptance,
the disposable PostgreSQL fixture, sandboxed Chromium, preparation/publication and persistent
routing. It explicitly does not claim product delivery. `factory.admission --activate` runs the
native scripted fixtures and records exact protocol/evidence hashes only after every check
passes. Actual migration/import/restore, frontend behavior and protected-main confirmation
belong to each product build and publication. Requiring the unfinished product before admitting
its own implementation formed a circular gate. Legacy schema1 receipts keep their original
strict requirements and cannot silently qualify the new external checker.

The live `prepared_product` adapter compiles a private candidate snapshot offline, starts only
the packaged app in its own container, then runs a frozen Node26 acceptance file in a different
container and PID/filesystem namespace. The verifier sees no candidate source or application
filesystem. Its immutable reporter emits numeric counts and bounded failure locations, not
response bodies, names or raw logs. A false assertion, missing report, skipped/todo/cancelled
case or a forged stdout report cannot pass. The author receives the frozen acceptance read-only.
The legacy same-JVM JUnit adapter remains for historical/offline fixtures.

A registered dependency transition seeds exact supervisor-owned Gradle/package bytes; the
worker cannot edit those files or choose versions. The frozen digest map, deterministic review
and isolated publisher bind approval to those exact bytes. An arbitrary request field cannot
approve another dependency. Nested Git control files are forbidden at both export/artifact
boundaries, preventing candidate ignore rules from hiding unreviewed code. Existing ignore rules are also checked before export reaches the host, so hidden environment or dependency files cannot influence acceptance outside the review packet. Product test harness
files may change only under the external checker; its program and contract are never writable.
The live author window comes from `demo/budget.conf` `AUTHOR_TIMEOUT_MINUTES` (5..180, default 30;
the shipped file sets 180, owner decision 2026-11-05); the worker lease grows with it and
`AUTHOR_MAX_USD` still stops spending first. Preparation/review remain at most900s per model session.
When the latest failed attempt at the exact same spec digest has a protected-check refusal, the
author prompt carries it as labelled data: the reason code, at most eight pattern-checked failing
test names and eight compiler locations, never output or source, and only while the prompt stays
within its 16000-byte bound (`Store.previous_check_failure`, test_factory_store/work_limits).
One owner launch makes at most three author attempts (`Store.MAX_ATTEMPTS`), each on a model
not yet used in that launch, and each attempt at most two correction rounds by its own model
(`Store.MAX_CORRECTION_ROUNDS`): at most nine author builds, each with its own window, reservation,
gate and two votes. A reviewer rejection or a failed final gate closes the build as `failed` and
admits, in the same transaction as its link `{previous_build_id, attempt, round}`, the next round,
or after the second round the next attempt. A retryable author stop (`RETRYABLE_AUTHOR_STOPS`:
CLI or provider failure, per-build budget, step, output or time limit, no patch, no eligible model)
starts the next attempt directly; scope, secret, revocation, sandbox, unknown cost or context
accounting, funds and credential stops end the launch (`test_factory_correction_rounds`). The next
author starts from the previous candidate only when its bytes still match the digest the failed
receipt recorded and the base is unchanged: a refused candidate, or after a crash the scoped files
the crashed author left, revalidated by `validate_artifact`. It receives the votes and check results
as at most twelve printable lines with secret-like text redacted, labelled as untrusted data, or
the crash code and error class. A required CI check that completed without success (`ci_failed`,
at most eight check names and conclusions, never a log or annotation) is the same kind of
refusal: the attempt becomes `failed` and the next correction is admitted in that same
transaction, starting from the published bytes when their digest still matches. A comma in a
check name is kept. A known check adds one fixed supervisor repair sentence, still without the
log. A correction that returned the same bytes after every stored check name was the placeholder
`check` is queued once more after those names are replaced (`repair_blind_ci`). The open pull
request is not merged and is not updated. Pending, unreadable and every other publication hold
stay held. When no correction remains, the attempt stays held for the owner
(`test_factory_publication_state`, `test_factory_github_atomic`). A correction that returns refused bytes unchanged is held
`correction_unchanged` without checks or votes (never after a crash, whose files nobody judged yet);
after the third attempt the owner decides. The runner keeps one error-class token from the author
CLI's stderr (`runner.error_class`: a CamelCase `…Error`/`…Exception`, `ERR_…` or a known POSIX
code), read in memory and never stored as text; build 96f9ddef (2026-11-06) exited 1 with no cause.
Every factory agent receives the same pipeline context (`demo/flue/src/context.ts`: OpenShell
without network, the goal, the five steps, the attempt bounds and the rules) and leaves owner-only
feedback, "RAS" or at most 800 characters: the author through the bridge `/v1/feedback`
(`submit_feedback`, one reminder before it may stop), reviewers and the preparer through an
optional field of their typed result. Notes land in the receipt `feedback`. A later correction
copies at most a few redacted lines into the next author's prompt as untrusted data, beside the
vote reasons. They never enter the vote, telemetry or memory. `factory.retention` removes, at controller start and
then daily, the workspaces of terminal builds older than seven days that no queued continuation
needs, and asks the publish role to delete the `aeion/build-*` branch of a failed or cancelled build
only when its pull request was closed without a merge (`test_factory_retention`). Every author prompt states that its OpenShell sandbox is not
the product runtime and that it must not change ports, routes, Docker or configuration defaults
the brief does not ask for: build 80463a43 (2026-11-06) passed every check but was rejected for
removing `/__release` and moving the default port.
Explicit operator bounds remain. `demo/budget.conf` sets the daily purse (at most $150, owner
decision 2026-11-07), one author execution (at most $50, reserved and relay-enforced) and one
review vote (at most $1);
an invalid file holds builds as `budget_config_invalid` and admits no spending. A soft stop can retain a proposed candidate
only after validated export, confirmed sandbox removal, complete known usage within the frozen
reservation and a current authorization check. Its stopped-role failure remains visible. No check
or vote is inferred: the final external gate and both independent reviews still run; unknown usage,
revocation and export/removal failures refuse recovery. A slow trace exporter uses a bounded SDK
batch queue so it cannot block native accounting; role shutdown flushes it. The private journal
remains authoritative when telemetry delivery fails.

Review envelope v2 includes a unified diff from the frozen Git base and the complete changed
files, MD and protected acceptance. Inherited code is distinguished from new work; future MDs
are not requirements for this incremental feature. Baseline blobs must be bounded, regular,
public UTF-8 files without credential-shaped values. Coverage and approvals bind base/diff
hashes; missing context holds before inference. Routing v5 preserves but excludes incomparable
old envelope outcomes. An explicit operator-only v1→v2 reassessment may reuse a known-cost
Flue proposal only when its exact main/task/artifact remains unchanged and publication never
started. A transaction archives the original rejection and increments the generation. It
reruns external gates and two fresh votes, including the original rejecting reviewer, excluding
the author/preparer. It never reruns or bills the author, imports a vote or repeats a v2 rejection.
Unknown usage, changed contracts, cancellation and prior remote work refuse this repair.
A reviewer must deliver its verdict through the typed `submit_review` tool. If a session ends
without it, the reviewer's Flue 2.3 `useAgentFinish` hook appends one result-required signal,
guarded by `usePersistentState` so it fires at most once; a second miss still fails closed with
`REVIEW_RESULT_MISSING`. The failed vote keeps its trusted execution metadata and failure code.
After a v2 hold caused only by such failures (no rejection), the controller reruns the
external gate and both votes once on the same unchanged artifact, without an operator and
without rerunning the author. `review_context --retry-failed-review` remains that same repair.
The archived votes are never reused. A second failure stays held. A same-build retry replaces
only that build's prepared folder and repo, and keeps a same-model resume clone. GitHub TLS
uses the system CA bundle when certifi is missing, and verification stays on. A reservation
for a claim that never forwarded settles at zero. A reservation whose usage was forwarded and
is still incomplete stays counted. Admission still counts both. The summary reports them apart.
The host relay tolerates up to 300s of upstream silence (connect or between bytes), because a
reasoning reviewer can think for minutes before its first byte; role deadlines still bound the
session. A stall is reported as `PROVIDER_TIMEOUT`, other socket failures as `TRANSPORT_ERROR`.
A busy provider (HTTP 408, 425, 429, 500, 502, 503, 504 or 529 before any byte) is retried
twice on the same claimed request, after 5s then 20s or an integer `Retry-After` capped at 30s;
closing the relay ends the wait. Other statuses, timeouts and socket failures are never retried.
A remaining 429 is `PROVIDER_RATE_LIMITED` and other busy statuses `PROVIDER_UNAVAILABLE`; the
last refusing HTTP status and the retry count stay in the role's execution metadata. A review
vote that ends with one of those two codes and zero output tokens produced no verdict, so its
slot goes once (`MAX_SUBSTITUTIONS`) to the next eligible reviewer outside the author, preparer
and earlier families; the busy attempt is kept as `unavailable_reviewers`, never as a vote, and
publication still needs exactly two independent approvals. A refusal, timeout or billed answer
still holds (test_factory_review_circuit, test_relay_budget_settlement). Measured 2026-11-05:
DeepSeek answered 429 twice on build ac5b5ce1 after its gate passed.
All100MDs declare their two owning product documentation files. Their shared scopes require
serial builds; completion still depends on the current contract and confirmed publication.
Preparation, the builder's repair feedback and the final gate share the same supervisor-selected
checker instance; a builder must not silently recreate a different database/check boundary
(test_factory_execution).

Shared checker tool provisioning is separate from untrusted execution. The pinned public
JDK/Playwright base images and exact npm lock build one non-root checker image, with no product
source, credentials or operator data in its build context. Dependency fetches occur only during
this trusted provisioning; candidates execute offline against read-only tools/caches and an
owned disposable loopback namespace. Browser sandboxing, negative controls and actual API/DB
fixtures must pass before the image can qualify PostgreSQL/React feature execution.
The [dated Chromium qualification](../../work/chromium-security-2026-11-03.md) records the
actual non-root namespace/Seccomp-BPF/TSYNC checks, absent Yama protection, pinned profile,
primary sources and the requirement to separate untrusted build processes from browser checks.

Disposable PostgreSQL separates its random bootstrap-administrator, migration-owner and
application credentials. The candidate application receives only the non-superuser application
role, with data access and no database/schema creation. Migration credentials remain with the
supervisor's isolated migration job; no static known owner password is shared with candidate
code. Native qualification proves ordinary reads/writes and refused application DDL/role changes;
these boundary checks do not certify product migration/restore or audit-specific grants.

Native inference uses OpenAI completions for GLM/DeepSeek and Anthropic messages for
Qwen/Haiku. The pinned Anthropic SDK appends `/v1/messages?beta=true`; its model base URL is
the relay origin, with a supervisor-issued stable conversation header. The relay admits only
the exact plain/beta paths and forwards to its fixed upstream; arbitrary queries cannot select
an endpoint. Haiku and Qwen require adaptive thinking with `max` effort before forwarding
(`test_provider_protocols`, Flue provider tests).

Owner rule (2026-11-06): every agent role thinks at its model's maximum, never medium. Each Flue
agent asks Pi for the `max` level and the provider adapter maps it to the native maximum: GLM
sends its Z.ai `thinking` object with `reasoning_effort: max`, DeepSeek `reasoning_effort: max`,
Haiku and Qwen adaptive thinking with `output_config.effort: max`. The relay refuses a GLM,
DeepSeek, Haiku or Qwen request that does not carry that exact effort; only a bounded review
recovery may ask for `low`. Measured 2026-11-06 on the paid Go endpoint: all four accepted their
maximum, and GLM's reasoning grew from 6 to 43 tokens between `low` and `max` on the same prompt.
The owner added two workers the same day. GPT-6 Luna (Go, family `openai`) validates
`reasoning_effort` and accepts `max`. Mistral Large 4 (family `mistral`) rejects `max` and `xhigh`,
so its maximum is `high`. It is not in Go: it runs on OpenCode pay-as-you-go, billed to the Console
balance at its list price (1.36/4.18 USD per 1M input/output tokens). Both send `reasoning_effort`
alone, and the relay refuses one with another value or a `thinking` object. They follow the four
measured models in the cold-start order.
The author also gets three protections, measured on build cca2f099 (GLM stopped 37 minutes after
its third and last allowed protected check had failed; about six shell commands hit the 300 s
command cap). Protected checks are no longer counted: the author window and the cost cap bound
them, and identical snapshots still reuse their cached result. A factory author that tries to stop
while its last check is missing or failed receives the failing tests and is told to continue, up
to three times (`MAX_FINISH_REMINDERS`); after that the unchanged final gate decides. The brief
forbids Gradle, Maven or other builds in the sandbox shell, which has no network, and names
`run_protected_checks` as the build and test runner (factory-checks.test.mjs, provider.test.mjs). Synthetic protocol qualification does not
establish provider acceptance, current billing/privacy evidence or model-quality ranking.

DeepSeek's native `thinking`/`reasoning_effort` protocol is explicitly mapped by the pinned
Pi1.4.0 adapter: low stays low, medium maps to high, max stays max. The relay enforces the supervisor's exact
effort before forwarding. After measured16384-output failures and a32768 budget-stop, the owner
requested looser local budgets under the existing$15/day ceiling. The full maintainer review
now runs at max effort (owner rule 2026-11-06), with a65536 maximum output and$1 per execution. Normal4096
defaults, the300k combined context ceiling and daily purses remain enforced. The first approval
and all failed attempts remain intact; rejection or unknown usage cannot retry. Public effort metadata
is retained in Langfuse and memory, never hidden reasoning; profilev3 separates measured cohorts.
The [DeepSeek thinking guide](https://api-docs.deepseek.com/guides/thinking_mode/) documents the
effort mapping/defaults (checked2026-11-03). Gateway acceptance is verified by the actual request,
not inferred from upstream documentation (provider.test.mjs,test_provider_protocols,
qualify_complete_review.py,test_factory_bootstrap).

The reviewer already receives the complete packet; it has no shell/file capability to reread
duplicate copies or attempt to run the product. The supervisor owns the real checks. A request
reserves its maximum input/output cost before forwarding; after complete provider usage, the
relay retains the larger of resource cost and conservatively priced input/actual output.
Unused output liability is then available inside the same unchanged dollar reservation. Input is
the counted input for a pinned tokenizer, or the provider-reported input for Qwen/Haiku, whose
admission byte bound runs about eight times the real count; reported cache reads are priced at
the cache-read rate, other input at the higher of the input and cache-write rates. Measured
2026-11-06 (build ea3fe718): settling on the byte bound stopped a Qwen author with BUDGET_STOP
after 20 requests at0.155 USD of its$2. When a request only appends messages to the previous one
(same model settings, cache markers ignored), its input is bounded by the previous reported input
plus the byte bound of the new messages; anything else keeps the full byte bound.

Go reports a plan `allowance` draw beside `list_cost`, at a fixed multiple of the list price per
model; the budget counts the larger. Measured 2026-11-06: GLM 1.33, DeepSeek 1.2, Qwen 2.67, Haiku
4, Luna 4; Mistral is charged to the balance at its list cost (1). Each profile carries this
`budget_multiplier` (rounded up); projections, settlement bounds and the harness estimate use it,
and a profile without one cannot run. Build df71b061 (Haiku author) stopped at 1.08 USD of 2 USD:
its allowance draw was four times the list estimate and the next request's byte bound did not
fit. The router also skips a model whose single request (whole output window plus 16384 input
tokens, at its multiple) exceeds half of its purpose's cap: Haiku at 0.70 USD per request does
not review (1 USD vote) or prepare (0.50 USD) (test_factory_budget_fit,
test_relay_budget_settlement). Missing
cost/output or unfinished streams retain their maximum liability; higher resource cost blocks
later calls. A known closed bootstrap failure caused by cumulative unused reservations may be
recovered once with the unchanged artifact and first approval, never unknown cost or a rejection
(test_relay_budget_settlement,test_factory_bootstrap).

The default output ceiling remains4096. A supervisor-bounded complete bootstrap review admits
at most240000 input bytes,65536output tokens,$1 and900 seconds, with per-forward cost admission
and the unchanged daily purse. Its exact reviewed CI documentation accompanies the source;
old frozen bundles remain readable. Pinned tokenizers retain the300k/20k preflight; Qwen/Haiku
use the measured context policy below. The model cannot increase these bounds. A length
finish is recorded as OUTPUT_LIMIT rather than opaque CLI_FAILED. Known-cost truncated attempts
stay recorded before an explicitly resumed review; unknown-cost attempts never auto-retry.

## Outputs

Metadata events and immutable receipts bind model/role/task/runtime, artifact/check/review
digests, usage basis, budget claims, memory acknowledgments and publication state. Missing
qualification, usage, checks, voters, privileges or expected base yields a visible hold. An
uncertain external action is reconciled before retry. A definite required-CI failure queues a
bounded correction; it is not a merge and not an unbounded retry. Uncertain cost never auto-retries.

A CLI stop (`CLI_FAILED`, `CLI_PROTOCOL_ERROR`, `HARNESS_COMPACTION`) after the session was
already working — at least three tool steps, three forwarded requests, or three tool or model
progress events — queues the same build again for the same model, at most three times, and
leaves the workspace in place. Paths that passed the path checks are kept for that resume even
when another path leaves the diff unaccepted; they are not published. A stop with no such
evidence, and `CLI_STARTUP_FAILED`, still starts the next attempt on another model from the
validated files. A provider error does too. A network stop resumes the same model even with
fewer steps. Before a paid call the live controller connects to the provider host twice; if
either connect fails the build holds as `network_unavailable` and no model is called, then
resumes when both succeed. An expired lease with that working evidence and no publication job
is queued the same way. Publishing, waiting for CI, or merging stays `reconciliation_needed`.
A reviewer `TRANSPORT_ERROR` retries that same model up to three times before `reviewer_failed`
(test_factory_correction_rounds, test_factory_connectivity, test_factory_review_circuit).
While no build lease is active, an OpenShell sandbox pair older than 30 minutes is removed.
A younger pair stays, so a qualification sandbox is not deleted while its owner is still
stopping it. A dispatched build keeps its sandbox (test_openshell_reap, test_factory_connectivity).
The controller loads that reaper by file path. The installed package owns the name openshell
and does not contain this repository's reaper.
Before a paid sandbox opens, a security proof with less than one hour left is refreshed by
the same host probe. The previous file is replaced only after that probe publishes the new
one. A failed probe holds the build as `sandbox_qualification_stale` and queues the same
build again when the proof is fresh, without another author attempt. A proof that has not
expired still allows the open (test_openshell_security_window, test_factory_correction_rounds).

## Invariants

1. Live authoring invokes Flue/Pi with tier-3 bridge tools; no direct-model or host-tool fallback.
2. OpenShell agent sandboxes expose no host mount, Docker socket, network or inference key.
   Inputs are bounded public bytes; output is validated before entering the candidate clone.
3. The lower tiers remain distinct: tier 1 in-memory triage, tier 2 confined file tools, tier 3
   sandboxed shell/files. Product implementation is always tier 3.
4. Profiles with a pinned local tokenizer reserve output/framing and refuse allocations above
   300000 before forwarding. Qwen/Haiku have no exact local tokenizer: their byte bound reserves
   cost only and cannot refuse a launch as a token count. They launch bounded inputs and gate the
   next call on complete API usage including cache; unknown usage holds, native250k hands over
   and native input+output above300k fails. There is no independent first-call300k preflight
   guarantee for these profiles. Handover remains supervisor-written, hashed and verified.
5. Model selection uses only comparable verified real outcomes, with deterministic tie breaks
   and explicit cold-start priors. No memory, trace, vote or agent can grant capability.
6. Two approving eligible models from different families, excluding the author and each other,
   must bind the complete identical artifact; missing/reject/error never means approval.
   A correction round or attempt is a new author build with two new votes, never a retried vote.
7. The publisher/merger has no inference role. It verifies stored evidence, required CI and
   exact PR head/base before a protected merge. A concurrent change invalidates approval.
8. Real data/history/budget liabilities survive restart. Synthetic qualification never marks
   a real feature implemented and never supplies model-quality ranking evidence.
9. Routing records are immutable and idempotent per attempt/role/model in the existing SQLite
   store. Only matching trusted area/size/architecture/check/runtime-method cohorts participate.
   Unknown costs remain unknown; ranking by observed cost requires complete measurements and
   at least three outcomes for at least two eligible models. Cold-start selection is explicitly
   labeled prior-based; a valid reject and a valid approve both measure protocol reliability,
   never independent proof that the review was correct. Unknown outcomes and no-forward budget/local errors do not count as measured model failures (test_factory_routing, test_factory_review_circuit).
10. Progress changes require the current dispatched attempt and cancellation generation.
    A cancelled or replaced attempt cannot overwrite displayed progress. Only fixed phases,
    allowed model identities and bounded counts/check statuses reach SSE (test_factory_progress).
11. Cancellation revokes future publication effects but cannot undo an in-flight remote merge.
    Unresolved publication keeps that feature unavailable. A late independently confirmed real
    main SHA is recorded as integration evidence without reviving the cancelled attempt;
    synthetic or unconfirmed responses never lock a feature as implemented
    (test_factory_publication_state).
12. A no-attempt dependency hold wakes automatically only for the unchanged admitted catalog.
    Queued or waiting requests from a changed catalog stay held as `catalog_changed`; no paid
    attempt is replayed and no request silently adopts new scopes/specs (test_factory_store).
13. Every factory model forward rechecks the current dispatched lease and cancellation
    generation; revocation stops the next request. An already forwarded call may still finish.
    Relay teardown waits for its final usage accounting; an unquiesced handler leaves usage
    unknown (test_factory_recovery, test_provider_protocols).

14. Generated acceptance is frozen and fully reviewed with the MD and artifact. Its preparer
    cannot build or cast either approval. A baseline initialization/compiler failure cannot
    substitute for an actual JUnit assertion failure (test_factory_preparation,
    test_factory_review_circuit, test_factory_vote_integrity).
15. Protected contract install/read/cleanup refuses candidate-controlled symlinks and confines
    all parent paths. Frozen contract drift fails before execution; cleanup never follows a
    replaced parent into host files. Candidate JUnit extensions, service providers, platform
    properties, foreign packages and skipped/unreported contract XML results are refused
    (test_factory_target_check, test_factory_live).
16. Completed role memory exports contain bounded identity/cost/check metadata only, with exact
    stored-record readbacks. Backends may fail without changing the role result or granting
    model/capability authority. Canonical outcomes remain in SQLite (test_factory_memories).
17. Completion and dependency evidence applies only to the exact feature metadata, canonical MD
    and approved architecture contract. Historical rows without that identity remain visible but
    cannot certify rewritten specs. Unrelated catalog edits preserve unchanged proofs. Admission
    may retire an obsolete queued/no-attempt hold, never a possibly paid attempt or uncertain
    publication. On-disk spec drift holds before preparation; legacy baseline verifiers cannot
    stamp a new architecture contract (test_factory_contract_identity).
18. Gradle build files, wrappers, settings, properties and version catalogs receive the same
    dependency-policy hold in the deterministic review and publisher. A model approval never
    authorizes a build-policy transition (test_factory_review, test_factory_publish).
19. A CLI stop while the agent was still working resumes the same build and the same model,
    at most three times, and does not admit another attempt. Fewer than three steps, a startup
    failure, or a provider error still starts the next attempt. An expired lease without that
    evidence, or one that reached publication, stays reconciliation_needed
    (test_factory_correction_rounds, test_factory_connectivity, test_factory_recovery).
20. A paid sandbox opens only when the OpenShell security proof has an hour or more left,
    or the host probe has just published a replacement. The previous proof is not removed
    first. A failed probe on an already expired or missing proof holds
    `sandbox_qualification_stale` and does not spend an author attempt
    (test_openshell_security_window, test_factory_correction_rounds).

## Determinism

Authority is deterministic and fail closed. Generated code/review text is untrusted. Decisions
and bounds are replayable from pinned inputs and recorded metadata, not model confidence.

## Acceptance checks

Run boundary, relay, factory/harness, routing and forge tests, real OpenShell isolation probes,
three-tier harness qualification and a real Flue/bridge/protected-check pipeline with local
fake inference/forge. Read back metadata from all three backends. Test stale heads, incomplete
CI, contradictory votes, unknown cost, malicious artifact paths and teardown failures.

## Out of scope

Direct pushes/force pushes to main, bypassed branch protection, external data in telemetry,
general benchmark claims, automatic policy tuning by memory, and unqualified fallback models.
