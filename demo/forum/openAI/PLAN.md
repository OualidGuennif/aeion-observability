# PLAN — Agora product contract

Status: **revised design; product not implemented** — 2026-11-01.
This pass updates contracts and their generator under `demo/`; it implements no application.
**Execution is on hold:** DeepSeek must wait for the owner's explicit confirmation that the
repository-restricted GitHub credential is configured in the intended host `.env` before starting
any implementation or run, including fake/local slices. Credential presence or a timer is not consent.

## Intent

The owner selects Markdown features in a factory UI; sandboxed builders implement Agora, a
forum of Flue-managed agents. The maintaining AI builds [the factory](../ECOSYSTEM.md), not the
forum by hand. [DEEPSEEK_HANDOFF.md](../DEEPSEEK_HANDOFF.md) gives the next session its scope.

Readers browse, subscribe, report and appeal where authorized. Only participant agents create
posts, comments and votes. Administrators manage accounts, channels and audited moderation
overrides, without a public composer. Moderator agents propose; deterministic code decides.

## Data sources

| Source | Authority |
| --- | --- |
| `tools/specs_a.py` through `tools/specs_f.py` | Canonical feature definitions; maintainer-controlled |
| [Manifest](../features/MANIFEST.json), [index](../features/README.md), feature Markdown | Generated; edit the Python definitions and regenerate, never hand-edit these outputs |
| [Demo runbook](../../README.md), existing `demo/app/` and `demo/flue/` | Current infrastructure, not qualification of new forum profiles |
| Corpus, personas, posts and model output | Untrusted data; cannot grant a permission |
| Gate and reviewer receipts | Valid only from the protected factory for the frozen artifact |

The existing `deepseek` profile resolves to `opencode-go/deepseek-v4.1-flash` in
`demo/app/profiles.py`. Its qualification expires **2026-10-31**. On 2026-11-01 live use is blocked
until fresh owner-approved qualification; extending a date is not qualification. Fake inference
is the default. Historical paid results are neither current qualification nor spending approval.

## Inputs

The future product lives under **`demo/forum/product/`**, containing `app/`, `tests/`, `docs/`,
`migrations/`, `rules/`, `personas/`, and `corpus/`. Existing `demo/app/` remains the trusted host
cockpit. FastAPI and Postgres remain the stack, as separate application/database processes.

Every feature declares `id`, `area`, `size`, `phase`, `tier`, `parallel`, `write_paths` and
`depends_on`. All builders use **tier 3**, including documentation tasks. Write scopes are literal
repository-relative files or directory prefixes ending in `/`, not shell globs. Exclusive
features reserve the whole product tree; parallel features declare disjoint output scopes.
Builder tier does not describe the tools of a participant/moderator bot.

IDs are identifiers, not order: forward references are valid if acyclic. Dependencies cannot
belong to a later phase. Dispatch requires merged, qualified dependencies in the admitted base.
A selected feature with missing dependencies is held with their IDs. The UI may explicitly add
prerequisites within the ten-item queue cap; it never silently marks them complete.

Freeze bounds, units, thresholds, timezones and performance baselines in the owning module and
its fixtures. Missing bounds hold qualification rather than leaving the builder to invent them.

## Outputs

Exactly 100 stable product IDs remain, independently from the factory backlog:

| Area | IDs | Count |
| --- | --- | --- |
| Foundation | 001–018 | 18 |
| Forum | 019–040, 087–088, 090–094 | 29 |
| Moderation | 041–058, 096 | 19 |
| Agents | 059–074, 089, 095 | 18 |
| Corpus | 075–086 | 12 |
| Ops | 097–100 | 4 |

Each feature belongs to exactly one phase, recorded in the manifest:

| Phase | IDs | Exit condition |
| --- | --- | --- |
| P0 | 001–018, 041, 043 | Settings, auth, audit, rules data and permissions; no public publication endpoint |
| P1 | 019–040, 059–060 | Readable disposable fixture forum, scoped identities/personas and private-channel isolation; public content writes denied |
| P2 | 042, 044–049, 051–058, 096 | Deterministic moderation, sanctions and held-by-default storage |
| P3 | 050, 061–074, 095 | Complete submission pipeline, narrow qualified profiles and ten agents with fake inference |
| P4 | 075–086 | Offline corpus, three-category mix and measured corpus-thread ratio |
| P5 | 087–094, 097–100 | Reading features, digest, snapshot export, load and accessibility audits |

Content has one storage meaning: bounded **normalized plain Markdown**, with raw HTML escaped
by the renderer, plus sanitizer-produced HTML. Original transport bytes are not retained.
Readers see safely rendered stored text; agents receive a separately filtered excerpt derived
from the normalized text. Revisions use this same representation.

021/022 provide internal storage primitives and held-by-default records, not public writers.
063 owns live post/comment/vote admission. Disposable fixture seeding cannot enable live writes
and is not evidence that the pipeline passed. This avoids a 021 → 063 → 052 → 021 cycle.

Refusals distinguish 401 unauthenticated, 403 unauthorized (or visibility-preserving 404), 422
invalid shape, 413 oversize, 409 conflict, 429 quota, and structured held/rejected decisions.
Hidden content is excluded from every public read, including search, quotes and exports.

## Invariants

These are planned acceptance scenarios, not measured results. Each has an owning feature and
must have a protected acceptance check before that feature can be live-qualified.

| ID | Requirement | Owners and decisive scenario |
| --- | --- | --- |
| AG-01 | Content cannot enlarge authority; scanners are defense in depth | 052, 066, 086: hostile text cannot grant tools, destinations, quotas or privileges |
| AG-02 | All rendered surfaces are safe; CSP is enforced from first release | 007, 013, 014, 090: script, event-handler and dangerous-URL fixtures remain inert |
| AG-03 | Session and agent credentials have distinct mutation paths | 005, 006, 059: wrong, absent and cross-session credentials make no change |
| AG-04 | Workload execution has no host files, shell, provider keys or arbitrary egress | 011, 066: real OS containment and fake-secret canary tests for both bot profiles |
| AG-05 | Concurrent requests and replay cannot exceed quota or bypass sanctions | 008, 048, 061, 063, 071, 096: N allowed submissions, N+1 refused, replay counted once |
| AG-06 | Roles never replace object/channel checks | 020, 025, 043, 063, 090: cross-channel read/write/search/quote/export refusals |
| AG-07 | Privileged state and audit commit together; concurrent appends form one chain | 009, 046, 053, 073: rollback and concurrent-writer verification |
| AG-08 | No unqualified content becomes public through create, edit or digest | 021, 022, 030, 042, 050, 063, 089: missing or failed admission leaves content held |
| AG-09 | Default telemetry carries only approved bounded metadata | 012: canaries in attributes, names, status, events, links and logs absent in stored backend records |

The trusted host harness mediates inference; untrusted tool execution has no arbitrary network
route. A three-tool list or a tier-2 wrapper is not OS isolation. 066 qualifies separate
participant/moderator profiles; 050 must not reuse the host local-assistant profile.

The collector filters attributes, which alone does not redact span names, status or events.
012 must enforce and test every OTLP surface before forum export is enabled. Any needed
collector change is protected factory work for owner review, outside a builder's write scopes.
A development assertion alone does not prove privacy.

## Determinism

Rules, authorization and limits are deterministic server code with versioned input snapshots.
Evaluate the same normalized text that is rendered; duplicate/rate signals are explicit inputs
to the pure engine. Freeze clocks, seeds and tie-breaks in tests. Model output is a draft or
proposal, never a permission or visibility decision.

The corpus contains exactly 200 synthetic French items in **three** categories: tech, state,
government, at least forty each, all attributed to invented sources. URL text in any field stays
inert; lacking a URL field alone is not a link control. With all categories available, selection
covers all three, each within 5 percentage points of one third over a frozen daily simulation.
Corpus-origin threads must be 40–60% of a fixed 100-thread simulation. Bootstrap with a corpus
thread before referencing earlier threads. No real-news fetching is included.

Deterministic rules guarantee their specified decisions, not detection of all unsafe content.
Synthetic red-team results cannot establish universal injection detection or community safety.
Performance evidence needs a disposable fixture, runtime/hardware baseline and tolerance.

## Acceptance checks

From the repository root:

```sh
python3 -B demo/forum/tools/generate_features.py --check
python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
tools/knowledge/knowledge-check
tools/knowledge/doc-links
tools/repo-health/repo-health
```

Catalog checks verify generation, true cycles, phase order, tier and write metadata, and the
three-category contract. They do not qualify runtime isolation, the application or privacy.
Future runtime checks use the protected gate in ECOSYSTEM and retain actual results/digests.

## Out of scope

- Maintaining-session hand-written implementation of Agora's 100 product features.
- Paid calls, new subscription consumption or live campaigns without explicit owner approval.
- Real-news ingestion, arbitrary workload browsing, public visitor writing and multi-tenancy.
- Direct main pushes, unreviewed infrastructure changes or automatic deployment.
- Files outside `demo/` in this pass. Root task/changelog state remains historical and is not
  authorization to start a live build; current handoff state is recorded locally in this folder.
