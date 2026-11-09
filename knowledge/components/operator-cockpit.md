---
type: Component
title: "Local feature cockpit"
description: "One administrator workspace for truthful feature availability, build activity and private traces."
status: draft
verified:
  - at: 2026-11-07
    what: "unittest live status: the report prints phase names and supervisor CI lines, and leaves reviewer prose out"
  - at: 2026-11-08
    what: "node cockpit client: a running protected check is not a stall; admission hours remaining are shown"
  - at: 2026-11-09
    what: "unittest kpis and selection: lab autonomy requires explicit zero human intervention and complete maturity; lab copy matches 150/50/1 ceilings and context policy"
sources:
  - resource: ../../demo/app/factory.html
    title: "Cockpit markup"
  - resource: ../../demo/app/factory.js
    title: "Cockpit client"
  - resource: ../../demo/factory/live_status.py
    title: "Read-only live status names"
  - resource: ../../demo/app/factory.css
    title: "Cockpit layout"
  - resource: ../../demo/app/server.py
    title: "Loopback routes"
  - resource: ../../demo/factory/api.py
    title: "Authenticated presentation"
  - resource: ../../demo/factory/store.py
    title: "Persistent admission guard"
  - resource: ../../demo/factory/target.py
    title: "Pinned source context"
  - resource: ../../demo/factory/agent_files.py
    title: "Bounded author input"
  - resource: ../../demo/factory/dispatch.py
    title: "Target preparation and execution"
---

# Local feature cockpit

## Intent

Make the default local page useful for selecting admitted product work and observing its actual outcome. Completed features cannot be selected or submitted again. The page opens with the owner's next step, then three status blocks (factory mode, today's budget, environments), then the catalog and build activity. The model lab at `/lab` is a showcase and playground for engineers (idea, architecture, stack, circuit, synthetic tasks, memory room), labelled as not needed to build features; its summary cards match the enforced $150/day, $50/author and $1/review ceilings and context policy, and its autonomy KPI counts only passed-check runs with explicit zero human intervention (`autonomy_basis: passed_checks_no_reported_intervention`). Both pages take every colour from `demo/app/theme.css` (light and dark sets) and offer an Auto/Light/Dark toggle (`demo/app/theme.js`, remembered per browser). The lab's memory room recalls Hindsight with a bounded question (`/api/memory?q=`, at most 160 printable characters) and reads back only checkpoints this observer wrote (`/api/memory/checkpoint/<id>`, metadata fields only); these helpers live in `demo/app/server.py` because `demo/app/memory.py` is protocol-hashed.

## Data sources

The authenticated catalog and SQLite build history supply feature availability. A baseline or merged record is implemented; a real completed attempt is built and awaiting integration. Simulation is historical evidence and never counts as implementation. A held request must be inspected and explicitly cancelled before a new launch. Validated per-feature targets restrict which features can run. A missing/broken target affects that feature, not the other configured targets. The shared budget ledger supplies reservations/settlements, not an invoice.

## Inputs

Existing administrator session, CSRF-protected queue/cancel calls, catalog IDs, search/status/phase filters and bounded SSE events. The browser cannot choose a repository, command, budget or target.

The initial view shows all specifications in prerequisite sequence. A global factory hold is
separate from missing feature dependencies, task preparation and review. No per-feature manual
setup is requested. Old dependency holds with no currently missing IDs are described as earlier
requests requiring reconciliation; an empty list never renders a broken prerequisite sentence.
Progress SSE updates display only fixed phases and bounded evidence, with measured routing
basis shown separately from an unmeasured cold-start default (client/progress/routing tests).

Authenticated `GET /api/factory/spec/<id>` returns literal Markdown and SHA256 for a known
catalog entry. A basename ending in `.md`, no symlink, a regular file and a 65536-byte maximum
are required. The dialog uses `textContent`, with stale-response suppression and keyboard
close; reading a spec never admits a build (test_factory_spec_preview). Missing/wrong sessions
and non-loopback hosts are refused by the same HTTP boundary as the catalog.

The catalog's optional `sequence` is a stable topological display order. Cards show that step
beside the immutable feature ID and phase; old fixture catalogs without it fall back to ID
ordering. Sorting a view must not mutate the server catalog or bypass availability checks
(test_cockpit_client). The 100-feature contract now targets the separate Quarkus/PostgreSQL/
React web product; regenerated specs do not perform that migration or qualify old targets.

The live controller prepares specifications through a shared product adapter rather than a
manual target JSON per feature. Native capability admission qualifies Flue/OpenShell, the
external verifier, PostgreSQL fixtures, Chromium, preparation/publication and routing mechanisms;
it explicitly does not claim that the product is already built. Every candidate still needs
its own external acceptance, two independent approvals and confirmed protected main.
Activity refreshes retain expanded build evidence and keyboard focus. An unchanged list is
not replaced, so reading evidence does not race the ten-second poll or SSE progress events.
The exact registered001/002/014 contracts prepare deterministically without model requests or cost;
changed MD bytes require fresh independent preparation. Missing acceptance format, explicit model
refusal, budget exhaustion, an invalid `demo/budget.conf` (`budget_config_invalid`) and unknown
usage have distinct bounded messages. A review vote that failed keeps its failure code (for example
`REVIEW_RESULT_MISSING` or `PROVIDER_TIMEOUT`) in the build evidence instead of a generic label. Private proposal
artifacts remain outside default telemetry. PostgreSQL/React helpers are not product delivery.
The transition baseline explains an absent registered migration operator or browser source.
A stopped author proposal can continue only with validated files, confirmed removal, complete
bounded cost and current authorization; the independent acceptance and two reviews still decide.
A failed build that queued an automatic continuation says so ("correction round N of 2" with the
same model, or "attempt N of 3 on another model" after the second round or a crash), and the next
build of the same feature appears in the queue without an owner launch. A required CI failure
uses that same sentence and names the failing checks; only the exhausted case stays on hold and
asks the owner to cancel. Build evidence says the rounds are finished only in that exhausted
case. A queued round says the check failed and the pull request was not merged. After the third attempt a
rejection is held with its reasons; a correction that changed nothing is held
`correction_unchanged` (test_factory_correction_rounds, test_cockpit_client). A round whose
required check name was stored only as `check` is queued once more after the real name is written. Build evidence shows the attempt and
round, the crashed author's error class and the agents' owner-only feedback as escaped text.
The controller removes terminal workspaces older than seven days at start and then daily
(`factory.retention`).
Build evidence includes the preparer (or registered static kind), negative baseline, memory acknowledgments,
publisher/CI blocker, confined PR link and confirmed main SHA. The actual user browser still
requires sign-in after a controller restart; synthetic browser/API verification is distinct.

## Outputs

Simulation and offline notices explicitly distinguish scripted work from live implementation,
paid inference and main publication. Queued and actively running counts are separate; a queued
request cannot be mistaken for a missing request (test_cockpit_client, browser fixture acceptance).
Completion locks match the current canonical feature contract. Historical proof remains visible
without certifying rewritten MDs; only an explicitly new admission retires an obsolete request
that has never started (test_factory_contract_identity).

The root and /factory serve the same cockpit; /lab serves the existing advanced lab. Catalog entries add availability (state, selectable, reason, missing dependencies). Board responses add the two purse summaries, or an unavailable budget state. A repeated completed feature is refused as feature_already_completed:<id>; an active duplicate is feature_in_progress:<id>. The API returns HTTP 409 for those admission conflicts. Idempotent replay retains the existing response.
A network hold says no new author was started and that the same request resumes when the provider answers again (test_cockpit_client). A stale OpenShell security proof says the same: wait, the factory resumes that request when the proof is fresh. A reviewer that returns no verdict says the controller reruns the votes once without rerunning the author, and that a second failure stays on hold. The budget block shows settled spend as the burned amount, then reserved capacity and what remains of the purse. Admission still counts open reservations. The copy names the owner ceilings of $150 per day, $50 per author execution and $1 per review vote.
While no build lease is active, the live controller removes an OpenShell sandbox pair only after it is 30 minutes old. A younger pair stays, including one still used by qualification. A dispatched build keeps its sandbox (test_openshell_reap, test_factory_connectivity). The reaper is loaded by file path, because the installed OpenShell package owns that import name.
`python3 -m factory.live_status` from `demo/` reads the listener and the factory database without opening the store. It prints status names, progress phases and, with `--feedback`, only the supervisor CI lines. Reviewer prose, receipts and credentials stay out. `--protection` prints the release token's branch-protection HTTP status and the required check names. A progress phase outside preparing, building, checking and reviewing is shown in the cockpit stage column as Build once a preparation exists; the stage sentence still names the step, for example Agent working (test_factory_live_status). While `protected_check.started` is the current phase, ten minutes of silence is not a stall: the clock says the protected check is running (test_cockpit_client). The catalog execution payload carries `admission_expires_ns`, and the notice says how many hours remain. Nothing renews that proof from the page. A failed draft check keeps at most eight pattern-checked test names on the progress receipt, so the Failed tests row can show them.

## Invariants

1. Completed or already active features are disabled in the interface and refused atomically in Store.admit, even with another request key or after reopening the store (test_cockpit_admission).
2. Simulation does not lock a feature as implemented; a candidate built by a real model is distinct from merged/baseline implementation (test_cockpit_admission).
3. Unsupported targets and unmet dependencies are visible before selection; backend execution gates remain authoritative (test_cockpit_admission).
4. Default activity separates current/recent real work from historical simulations. Raw receipt data is behind details; trace confirmation remains explicit (browser fixture acceptance).
5. Per-build target selection uses the selected feature brief/scopes/check; unknown targets hold before a budget reservation, and unexpected worker errors become visible holds without an automatic paid retry (test_factory_feature_targets).
6. No launch or release call occurs on page load. The cockpit no longer shows the synthetic
   canary drill; its environment block states Staging and Production as "Not deployed yet" until
   a real deployment receipt with deployed-source/readiness evidence exists (test_cockpit_client).
   The drill API remains server-side history only and never supplies an environment link.
7. Authentication, CSRF and loopback binding remain required. No credential is stored in browser persistent storage.
8. While the author runs, its card shows elapsed time against the configured window
   (`author_window_seconds` from the board), time since the last tool or model step, and the
   count of failed draft self-tests. A repeated cached failure, a check that raises, and a
   second identical finished failure count in that total. The identical repeat does not add
   another progress event and does not move the silence clock. Ten silent minutes or three failed drafts raise a visible
   warning; the window and author budget remain the only stops (test_cockpit_client).
   A passed gate is not replayed to the next author as a failed self-check, and it hides an older failure of that same spec.
9. Claim, completion, cancellation, hold and recovery preconditions are serialized across Store instances. The worker lease covers configured preparation, author, protected-check and two-review deadlines plus teardown. An expired attempt with no evidence the agent was still working holds as reconciliation_needed, preserves attempt identity, and does not start another paid action (test_factory_recovery). An expired attempt whose tool or model progress shows it was still working, and that has no publication job, is queued again for the same model at most three times (test_factory_connectivity). A live paid controller that cannot reach the provider twice holds the build as network_unavailable and starts no author; the cockpit says to wait rather than relaunch (test_cockpit_client).
10. Compiler failures expose bounded filenames, line numbers and identifiers, never source lines,
    values or complete compiler output (test_factory_target_check and test_cockpit_client).
11. Independent review receives all changed files within the bounded complete-review envelope; larger
    input still holds before any vote and no excerpt can approve an artifact (test_factory_modelfarm).
12. Optional target context names at most eight public main Java files. Only regular blobs
    from the exact pinned commit are read, never working-tree changes, symlinks, configuration
    or credentials. Each file is bounded to 24000 UTF-8 bytes and the full labeled context to
    48000 bytes. The dispatcher supplies it outside candidate write scopes and the author
    receives complete bytes, with oversized input refused before transport
    (test_factory_source_context).
13. A "Your next step" banner names exactly one plain owner action, derived from execution mode,
    factory hold, the current held build (review-circuit reason first), a running build or ready
    features, in that order. Simulation and offline modes say nothing real can be built
    (test_cockpit_client).

Target 007 adapts content sanitization to the current JSON forum. Its external contract
checks normalized stored Markdown, safe derived body_html on create/read/list, a conservative
Markdown subset, 30 hostile payloads, codepoint/body bounds and refusal without a new outbox
event. The existing database schema, plain-text mobile client and canonical catalog remain
compatible. Qualification uses isolated state and an injected candidate; it never marks the
real feature implemented or spends on a model. Only the owner's real cockpit launch builds it.

The old direct model-call engine and staging/publish entry points have been removed. Live
execution has one Flue/Pi path; exported files still pass the shared bounded validator.
Its default state is separate from real builds. The existing authenticated cockpit remains the
real authoring entrypoint (test_factory_legacy_cli).

Verified local implementations may enter through baseline.py: 017 requires its exact pinned
product target and an injected external contract, not just a broad passing build. Its immutable
proof and best-effort metadata trace persist on the baseline receipt; it never claims model
authoring or two-model approval (test_factory_baseline).

## Determinism

Availability is derived deterministically from supervisor-owned records and the configured execution. Existing SQLite transactions serialize admission. Presentation cannot satisfy dependencies or rewrite execution policy.

## Acceptance checks

Run demo/tests/test_cockpit_admission.py, demo/tests/test_factory_live_status.py, the existing demo suite, knowledge-check and doc-links. Verify the actual rendered interface using a temporary fixture backend with a fixture administrator token: completed/active/unsupported rows cannot be selected; ready selection enables the launch control; filtering, trace details and narrow layout remain usable. Do not spend on a model merely to validate presentation.

## Out of scope

History deletion, permission expansion and unrelated provider evaluations remain outside
this delivery. Product business code belongs to dispatched product workers, not Observer mirrors.
