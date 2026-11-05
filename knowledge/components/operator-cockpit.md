---
type: Component
title: "Local feature cockpit"
description: "One administrator workspace for truthful feature availability, build activity and private traces."
status: draft
sources:
  - resource: ../../demo/app/factory.html
    title: "Cockpit markup"
  - resource: ../../demo/app/factory.js
    title: "Cockpit client"
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

Make the default local page useful for selecting admitted product work and observing its actual outcome. Completed features cannot be selected or submitted again. The model lab remains available as an advanced view.

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
The exact registered001 contract prepares deterministically without model requests or cost;
changed MD bytes require fresh independent preparation. Missing acceptance format, explicit model
refusal, budget exhaustion and unknown usage have distinct bounded messages. Private proposal
artifacts remain outside default telemetry. PostgreSQL/React helpers are not product delivery.
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

## Invariants

1. Completed or already active features are disabled in the interface and refused atomically in Store.admit, even with another request key or after reopening the store (test_cockpit_admission).
2. Simulation does not lock a feature as implemented; a candidate built by a real model is distinct from merged/baseline implementation (test_cockpit_admission).
3. Unsupported targets and unmet dependencies are visible before selection; backend execution gates remain authoritative (test_cockpit_admission).
4. Default activity separates current/recent real work from historical simulations. Raw receipt data is behind details; trace confirmation remains explicit (browser fixture acceptance).
5. Per-build target selection uses the selected feature brief/scopes/check; unknown targets hold before a budget reservation, and unexpected worker errors become visible holds without an automatic paid retry (test_factory_feature_targets).
6. No launch or release call occurs on page load. The release drill is loaded only when its advanced panel opens (browser fixture acceptance).
7. Authentication, CSRF and loopback binding remain required. No credential is stored in browser persistent storage.
8. Claim, completion, cancellation, hold and recovery preconditions are serialized across Store instances. The worker lease covers configured preparation, author, protected-check and two-review deadlines plus teardown. Expired attempts hold as reconciliation_needed, preserve attempt identity, and never automatically repeat an uncertain paid action (test_factory_recovery).
9. Compiler failures expose bounded filenames, line numbers and identifiers, never source lines,
   values or complete compiler output (test_factory_target_check and test_cockpit_client).
10. Independent review receives all changed files within the bounded complete-review envelope; larger
    input still holds before any vote and no excerpt can approve an artifact (test_factory_modelfarm).
11. Optional target context names at most eight public main Java files. Only regular blobs
    from the exact pinned commit are read, never working-tree changes, symlinks, configuration
    or credentials. Each file is bounded to 24000 UTF-8 bytes and the full labeled context to
    48000 bytes. The dispatcher supplies it outside candidate write scopes and the author
    receives complete bytes, with oversized input refused before transport
    (test_factory_source_context).

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

Run demo/tests/test_cockpit_admission.py, the existing demo suite, knowledge-check and doc-links. Verify the actual rendered interface using a temporary fixture backend with a fixture administrator token: completed/active/unsupported rows cannot be selected; ready selection enables the launch control; filtering, trace details and narrow layout remain usable. Do not spend on a model merely to validate presentation.

## Out of scope

History deletion, permission expansion and unrelated provider evaluations remain outside
this delivery. Product business code belongs to dispatched product workers, not Observer mirrors.
