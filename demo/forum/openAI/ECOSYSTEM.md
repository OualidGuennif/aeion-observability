# ECOSYSTEM — the factory that builds Agora

Status: **implemented local factory; Flue/Pi live-engine completion in progress** — 2026-11-03.
The owner has explicitly authorized the engine replacement, automatic protected publication to
main, and the [Quarkus/PostgreSQL/React web target](../ARCHITECTURE.md). The November 1 startup
hold has been superseded by those instructions. Missing current runtime qualification still
holds dispatch. Presence of credentials alone never grants additional authority.

## Intent

Add `/factory` to the loopback cockpit: select one of 100 Markdown features, queue up to ten,
and watch sandboxed builders return checked artifacts. Product code goes in the separate product repository under the paths in ARCHITECTURE.md;
trusted factory code lives in observer `demo/factory/`.
Existing `demo/app/` and `demo/flue/` remain trusted infrastructure, excluded from builder writes.

| Actor | Allowed work | Boundary |
| --- | --- | --- |
| Owner | approve policy, sensitive changes and deployment | Can revoke authority |
| Maintaining AI / DeepSeek | implement and test the factory locally | Does not implement Agora by hand or grant itself credentials |
| Builder | one frozen product feature | No credentials, publishing, merging or writable factory files |
| Observer | bounded metadata; deduplicated issue/PR proposals | No forge token, merge capability or raw transcripts |
| Host publisher | approved repository operations | Deterministic checks of target, artifact, approval and cancellation |

## Data sources

- Canonical `demo/forum/tools/specs_*.py`; generated feature Markdown, index and manifest.
- Current entrypoints: `demo/run.py`, `demo/app/server.py`, `demo/app/runner.py`, `demo/flue/`.
- Supervisor-owned SQLite state under ignored `demo/.local/factory/`.
- A maintainer-owned protected check bundle, acceptance registry and authorized review receipts.
- Builder/observer output, candidate code, UI-rendered Markdown and workload events are untrusted.

Preserve the current branch and concurrent work. Required checks and branch protection must be
verified on the actual product repository; neither the observer CI nor a local hook proves that
product merges are protected.

## Inputs

Freeze `build_id`, feature/spec/manifest digests, target repository ID, base SHA, phase,
dependency receipts, tier=3, literal write scopes, model profile/mode, deadline, step cap, context
limits and a cost reservation in USD. Unknown fields, missing bounds, expired profiles or
unqualified dependencies hold the build. Model output cannot override any of these fields.

Queue insertion uses an idempotency key bound to IDs and catalog digest. Replaying the same
payload returns the same result; a different payload conflicts. At most ten nonterminal builds,
including running builds, are admitted. Initial active concurrency is one; after exclusivity
checks it can be configured up to two. Concurrent candidates must both declare `parallel: true`,
have no dependency between them and have disjoint write scopes; otherwise run serially.
Use separate worktrees, never a shared mutable checkout.

SQLite transactions claim work and record transitions/events atomically. One supervisor holds a
process lock and runs one tick. Persist attempt ID, lease and cancellation generation before
starting a worker. On restart, reconcile expired leases and uncertain effects; never blindly
redispatch an attempt that may already have published.

Give the builder a bounded read-only brief/interfaces from the frozen base and a private
product worktree. No host Git config, credential helper, SSH agent, Docker socket, sibling tree,
transcript, provider key or writable Git metadata. The host commits a validated artifact bundle;
model-generated shell text never runs on the host.

The maintainer supplies the trusted participant/moderator broker integration as factory work.
Product feature 066 qualifies that interface and its product-side adapters; it cannot modify
the host harness. Host code must never import or execute candidate product modules. A missing
broker integration holds qualification rather than expanding a builder's write scopes.

All builder tools run in OpenShell tier 3 with no workload egress. Trusted host inference uses
the existing relay. The qualified local transport uses RPC copy-in/out with no host mounts; its receipt binds the
actual platform, runtime, image and policy. Missing or stale receipts hold live dispatch. A
macOS result does not qualify Linux automatically.
A stand-in is labelled simulation, never containment evidence.

Dry-run uses fake inference and a disposable local repository, producing a local PR-shaped
receipt, not a GitHub PR. It exercises real transitions/policy but cannot satisfy real product
dependencies or generate a real merge receipt. Waking DeepSeek does not authorize paid or
subscription calls. Every live model/runtime pair requires fresh capability, privacy and harness qualification. Reserve exposure atomically across builders and observer before inference;
missing usage is unknown, never zero. Per-build and aggregate caps, time and step limits all
apply independently. No cap configured means no live admission.

## Outputs

The board shows ID, title, phase, area, size, tier, parallel flag, dependencies and state; sanitized
spec previews; Build/Queue; missing-dependency explanations; live attempt rows with steps, time,
usage coverage, checks, verdict and a validated PR link. SSE is bounded metadata with reconnect
cursors; reload reconstructs state from the server; the cockpit remains independent of the product React client. Simulated runs and unknown cost remain explicit.

Factory reads, SSE and mutations require a dedicated administrator session. Bootstrap outside
the browser; rotate on login; enforce idle/absolute expiry, HttpOnly/SameSite, Secure over TLS,
CSRF for mutations, Host/Origin checks, body/rate limits and server authorization per action.
Forum reader sessions cannot access factory APIs. Escape Markdown/labels. S1 must prove wrong,
missing, expired and cross-origin credentials cannot read private state or trigger a build.

States are `proposed → queued → dispatched → built → gated → pr_open → approved → merged`, plus
`held`, `failed`, `cancelled`, and the distinct dry-run terminal `simulated_complete`. Every
transition verifies previous state, attempt ID and cancellation generation, then records actor,
time, reason and artifact identity atomically. Dependencies require a real merge plus protected
qualification in the admitted base, never simulation or a self-reported result.

Stable holds: `dependency_missing`, `profile_expired`, `sandbox_unqualified`, `budget_unavailable`,
`qualification_missing`, `owner_review_required`, `reconciliation_needed`. A failed gate names
its failing check. Retry is an explicit new attempt; two failures produce one deduplicated
observer proposal rather than an automatic repair/spending loop.

## Invariants

| ID | Requirement | Planned acceptance scenario |
| --- | --- | --- |
| FX-01 | Builders can write only their product scopes | Real tier-3 parent/absolute/symlink/host/sibling escape attempts all refused |
| FX-02 | A builder cannot weaken its evaluator | Candidate tests always pass, but a failing protected case still blocks |
| FX-03 | Gate, review and merge certify the same admitted artifact | Change head/base after validation; stale evidence cannot publish or merge |
| FX-04 | Replay/concurrency cannot duplicate authorized effects | Duplicate HTTP requests and simultaneous ticks yield one claim/receipt per attempt |
| FX-05 | Cancellation revokes effects, not just display state | Cancel during inference, after gate, before push/merge; late output cannot advance |
| FX-06 | Observer proposals cannot enlarge forge authority | Requests for another repository, protected path or merge are refused and audited |
| FX-07 | UI/telemetry exclude secrets and content | Fake canaries absent from errors, SSE, all OTLP surfaces and stored backend records |
| FX-08 | Recovery reconciles uncertain publication | Crash after PR creation before local recording; restart discovers one existing PR |
| FX-09 | Concurrent exposure stays inside admitted caps | Competing reservations at the cap cannot both succeed; unresolved usage blocks exposure |
| FX-10 | Explicit owner authority and current qualification are both required | Credentials without authorization or a stale qualification cannot dispatch a worker |

The kill switch first persists disabled dispatch and increments the cancellation generation.
Revoke active relay admission, terminate owned process groups within a configured deadline, and
reject pending publish/merge requests. External effects already completed must be recorded and
reconciled. Re-enabling requires an administrator action and a new attempt, never stale authority.

## Determinism

### Gate and artifact identity

Bound and validate the artifact bundle before making a host commit. Reject out-of-scope,
absolute/traversal paths, symlinks, submodules, non-regular entries, Git metadata, ambiguous path
encodings and unknown output types. Renames validate both endpoints. Inspect the actual Git
diff, never trust a reported path list. Product processes never run on the host.

Run gates in a fresh network-denied sandbox without host/provider/forge credentials. App tests
are useful but untrusted. Also run a **protected check bundle** from an approved factory revision,
read-only outside the candidate tree. Protect fixture/import/config resolution against candidate
replacement. Run Factory check implementations from that approved revision against candidate
data, not a candidate copy of the evaluator. Missing feature qualification holds dispatch.

The verdict binds repository, feature/build/attempt, base/head SHA, tree/spec/manifest/check-bundle
digests, all required results and cancellation generation. The authorized reviewer is distinct
from builder and observer and reviews that exact diff. A candidate-written receipt, self-report
or arbitrary `Review: OK` comment is insufficient. Store receipts in supervisor-owned storage,
validate issuer/revision, and re-read real head/base before effects. Base changes require fresh
integration checks and review as applicable; do not reuse a green result for another tree.

### Merge policy and GitHub credentials

Builders and observers have **no GitHub token**. The publisher accepts only a repository ID and
branches pinned by owner configuration. Local work needs no token. For remote operation, the
owner installs a GitHub App on this repository only (preferred for the persistent service), or
supplies a restricted fine-grained PAT through protected host credential storage. Never put its
value in a file committed here or in a brief.

Grant Contents write, Pull requests write, Issues write, and Actions read only if needed for
check readback; Metadata read is implicit. No account/organization, Administration, Workflows,
Secrets or Environments permissions. Do not promise Checks API support for a fine-grained PAT;
qualify the actual readback endpoint/token pair. Merge needs Contents write, not only Issues/PR.
Other public repositories remain publicly readable, so 200 on one is not a scope failure.
[Token documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
and [merge API](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request), checked 2026-11-01.

- No direct push to `main`. The owner has authorized automatic feature PRs targeting `main`
  after exact-artifact gates, two approving independent model reviews and required CI. A merge
  is complete only after confirming its resulting SHA on main; an open PR is not completion.
- Auto-merge eligibility is restricted to the **separate product repository paths in ARCHITECTURE.md**, intersected with frozen
  feature write scopes and the reviewed actual diff. A product prefix alone is not approval.
- Always require owner review for migrations, auth/security/moderation/rules/runtime configuration,
  dependency manifests/locks, deployment and permission changes. Sensitive behavior moved into
  another filename remains sensitive; path filtering cannot replace review or qualification.
- Factory, cockpit, harness, collector, specs/manifests, protected checks, `.github/`, `tools/`,
  credentials and other projects are excluded. A mixed diff holds as a whole.
- Require fresh protected green gates, authorized exact-SHA review, active noncancelled attempt
  and publisher approval. Supply the expected head SHA at merge; require the tested base still
  current or hold for revalidation. Record the resulting real merge SHA.
- Refuse remote mode until branch existence, required CI on main PRs, stale-review
  invalidation and protections against direct push, force-push and deletion are verified. Required
  results have a trusted issuer. The publisher cannot bypass protections. Workers cannot edit `.github/`
  or remote settings. Any protection preparation is trusted maintainer work under explicit owner authority.

Use deterministic attempt IDs for branch/PR lookup and reconciliation. On timeout, query the
result before retrying. Local pre-push hooks do not enforce server-side merges. Never switch
repo mode or disable protections to get a green result.

## Acceptance checks

These are acceptance milestones; this document alone does not certify their completion:

| Slice | Deliverable | Proof |
| --- | --- | --- |
| S1 | local board/API, SQLite queue, fake worker, SSE, cancellation | ten-item cap; missing dependencies; exclusivity; auth/CSRF refusals; replay/restart; simulated terminal state |
| S2 | frozen dispatch, tier-3 adapter, artifact/commit publisher | fake inference through real containment; escape/canary refusals; local scratch branch and honest PR-shaped receipt |
| S3 | protected gates, reviewer/publisher policy, observer proposals | allowed/outside/mixed/sensitive diffs; altered tests; stale head/base; cancelled attempt; crash-after-publication |
| S4 | local VPS configuration/runbook and backup/restore drill | disposable factory-SQLite/product-PostgreSQL restore with matching counts/digests/audit chain, then health/auth/TLS checks |

S1 uses labelled fixtures for dependencies, never marks the real catalog merged. S2 is not an
automatic paid run. S3 uses a fake forge until remote operation is explicitly enabled. The
observer reports meaningful changes, failures or required actions, not mandatory daily messages.
S4 prepares local artifacts; actual VPS deployment remains the owner's action.

Run the catalog checks in [PLAN.md](../PLAN.md), then relevant existing demo/Flue checks for runtime
changes. Add focused factory behavior tests during implementation. [VALIDATION.md](../VALIDATION.md)
records this documentation pass; its checks do not qualify any runtime slice.

## Out of scope

- Direct implementation of the 100 product features by the maintaining session.
- Paid/live inference, remote push/PR/merge, credentials, branch changes or deployment triggered by
  this update or by the model waking up.
- Sibling projects, billing, account permissions or agent-controlled branch protection.
- Treating synthetic examples, mocked sandboxes or documentation checks as runtime qualification.

## Release plane

How a built release leaves staging, how much traffic it gets and when, how flags travel with it and
how the workers that build it authenticate: [RELEASES.md](../RELEASES.md). The code is
`demo/factory/release.py`, `demo/factory/canary.py`, `demo/factory/releases.py`,
`demo/factory/gateway.py` and `demo/deploy/`.
