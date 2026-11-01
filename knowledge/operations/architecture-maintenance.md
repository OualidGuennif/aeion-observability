---
type: Runbook
title: "Graphify and Archify maintenance"
description: "Recommended local baseline installed only on the user's yes, and the CI exact-commit refresh after every main update, without model credentials."
status: stable
review_after: 2027-01-29
generated:
  by: aeion-factory/1.1
  at: 2026-10-25
sources:
  - id: refresh
    resource: ../../tools/architecture/refresh
    title: "Immutable snapshot, graph and diagram gates"
  - id: graph
    resource: ../../tools/architecture/graph.py
    title: "Native Graphify structural extraction"
  - id: setup
    resource: ../../tools/architecture/setup
    title: "Isolated pinned integrations"
  - id: pins
    resource: ../../tools/architecture/integrations.json
    title: "Reviewed revisions and scope"
  - id: views
    resource: ../../tools/architecture/views.json
    title: "Maintained source-backed architecture views"
  - id: ci
    resource: ../../.github/workflows/architecture-refresh.yml
    title: "Pull request and mandatory post-main analysis"
  - id: tests
    resource: ../../tools/architecture/tests/test_refresh.py
    title: "Coverage, provenance and failure regressions"
  - resource: ../../tools/architecture/process.py
    title: "process.py, which names this doc as its spec"
  - resource: ../../tools/architecture/gallery
    title: "Single-file diagram gallery"
  - resource: ../../tools/architecture/tests/test_gallery.py
    title: "Gallery inlining and refusals"
---

# Architecture maintenance

A local baseline is strongly recommended and never installed automatically. An agent asks the
user before running `tools/architecture/setup`, says what it installs (below), and asks whether the
machine is a work computer whose policy restricts installs. On a yes, run setup, then
`tools/architecture/refresh --target HEAD`. Without a baseline the launchers warn and continue;
CI still runs the analysis on GitHub, for the release pull request `develop → main` and every main
update; pushes to `develop` run none. Setup creates a virtual environment in `.aeion/integrations/`,
downloads the reviewed Graphify revision and its pinned packages into it, and clones the pinned
Archify package there. Both pins are release tags (Graphify 0.9.97, Archify v3.2.0), recorded by commit
in `tools/architecture/integrations.json`. Git, Python 3.12+ (excluding 3.14.1), Node 18+ and Chrome/Chromium are
required. Dependencies and browser execution are explicit; there is no global plugin install.
Setup reinstalls the Graphify source pin even if the same package version was installed from a
different source; refresh verifies its immutable commit archive URL and SHA-256 before importing it.

The same refresh command runs on every push to main, including docs-only and multi-commit
updates. A PR also runs it before merge. No branch-wide concurrency key drops older jobs.
The workflow uploads one immutable artifact per SHA and run; it has no write permission and
cannot commit generated output. A failed post-merge round blocks closure/release, not history.

Each refresh freezes the target into a temporary clean Git clone, scans only the manifest's
allowed tracked text, excludes secret names (the shared list in `.claude/hooks/secret_names.py`)
and symlinks, and invokes pinned Graphify's native
structural code/Markdown/config extractors. Each round rebuilds the small complete corpus so
deletions and renames cannot leave old nodes. Required code/Markdown with no extracted node
fails coverage. Other files are explicitly listed as inventory-only. PDF/image semantics and
LLM inference are not claimed. This deterministic baseline needs no model token or secret.

The context lifecycle view follows the shared rule of [context safety](context-safety.md) for all
four harnesses: 250k closure, verified checkpoint, compaction, and a 300k state that forces the
handover and compaction again instead of a stop.

**Plain folder.** `refresh` needs the root to be its own git repository and refuses otherwise, before
any git call: nested in another repository, git would answer for the parent. In a plain folder, run
the two steps directly, with the parent's toolchain: `.aeion/integrations/graphify-venv/bin/python
tools/architecture/graph.py <root> <out> <manifest.json>` (the manifest lists `{path, required}`),
then `node .aeion/integrations/archify/archify/bin/archify.mjs render <type> <input.json> <out.html>`
and `browser-check <out.html>`. Archify's evidence links need a git SHA, so a plain folder's diagrams carry none.
`archify examples` is not a listing: it rewrites the example HTML inside the Archify checkout (a sandbox
refuses it). To learn a diagram type, read the pinned schema and example JSON files there instead.

**Gallery.** `tools/architecture/gallery <render>` reads `<render>/diagrams/<name>.json` (Archify inputs; its
receipts are skipped) with the rendered `<name>.html` beside each, plus an optional `catalog.json` list of
`{name, question, group}`, and writes one `<render>/index.html` that inlines every diagram as a lazy iframe
`srcdoc`. Browsers block iframes of sibling files from `file://`, so this is the page that opens from
disk with no server. Rendered HTML is generated, never tracked: commit the JSON. A diagram without its
render is refused, and nothing is written.

**Working graph.** The baselines are immutable per commit. For questions while editing, the skill
`graph` uses [`tools/architecture/ask`](../components/graph-queries.md): it rebuilds `.aeion/graph/`
from the working tree when a file changed, in a git repository or a plain folder alike, and answers
from it without the venv.

The canonical [architecture spec](../components/factory-architecture.md) and `views.json` are
reviewed source, not generated policy. Runtime/config changes must update the architecture spec
in the same diff (or carry its existing `Docs-Checked` trailer). Reviewers verify semantic
completeness. Refresh validates source anchors (one to three per node, Archify's limit), pins diagram provenance to the target SHA,
and runs Archify `finalize` for every view, including browser checks. A browser/gate failure
is not success. Automated gates cannot prove semantic correctness or visual quality.

Outputs live in `.aeion/analysis/<sha>/`: graph, report, coverage/source manifest, diagrams,
Archify receipts, and an Æion Factory `receipt.json`. Publication uses a lock and atomic final receipt.
Archify renders at its permanent target path because moving its HTML invalidates native path
provenance. Incomplete attempts have no PASS receipt; invalid prior attempts are retained aside.
A same-SHA successful rerun verifies artifact hashes and all gate summaries before reuse.
There is no shared writable cross-job graph cache.
`tools/architecture/refresh --check --target HEAD` verifies all artifact hashes at launch.
No mutable latest pointer can be moved backward by an older finishing job. Each run instead rebuilds
`.aeion/analysis/index.html` from the PASS receipts, newest commit first; `docs/diagrams.html` links it.
Downloaded CI artifacts preserve the original run's evidence and portable hashes. To revalidate
Archify path provenance in a different location, run a new local baseline for that SHA.

Use `--base <sha>` to record the complete changed/removed path set and validate spec coverage.
PR diffs use the merge base of the supplied base/head, so independently advancing main does
not reject a valid branch; the immutable baseline receipt records its original requested base SHA and effective merge base.
Every invocation also writes `.aeion/analysis/comparisons/<target>/<requested-base-or-initial>.json`
with the current comparison and baseline-receipt hash. This preserves graph reuse without reporting
an earlier changed-path set as the current comparison.
Missing refs fail. With no base this is a full initial baseline, not an implicit empty diff.
The workflow supplies the PR base or push's previous SHA; an all-zero initial-push base means
a full baseline. Paths outside the declared scope are listed, never silently marked extracted.
When adopting Æion Factory, update both the scope/views and the project architecture spec first.

Commands: `python3 tools/architecture/tests/test_refresh.py` and the real refresh command above.
Release/ship checks must wait for the exact merged SHA's analysis check. A rerun retries that
same SHA; no automatic PR, message, spec rewrite, push, deploy or provider call is performed.
