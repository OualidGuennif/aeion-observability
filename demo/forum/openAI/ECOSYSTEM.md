# ECOSYSTEM — the factory that builds Agora

Status: **design, being built by the AI, 2026-11-01**. This file is the counterpart of
[PLAN.md](PLAN.md): PLAN describes the product (Agora, 100 features); this file describes the
machine that builds it. The machine is not a backlog item for an agent — it is the work this
repository does itself.

## 1. Who builds what

| Actor | Builds | Never |
| --- | --- | --- |
| Owner | decisions, review, the VPS deploy | — |
| AI (this repository, this session) | the factory: front, queue, dispatcher, gates, cockpit views, deploy runbook | the forum's features by hand |
| Builder agent (Flue, dispatched) | one feature file at a time, in a sandbox | merging, branch protection, secrets |
| Observer agent (Flue) | issues, triage, PR proposals | merging outside the allowlist |

The forum is never written directly here. Every line of it comes out of a dispatched feature and a
verified pull request. That is the point of the whole design.

## 2. The front

One page in the existing cockpit, `/factory`, on loopback: `python3 demo/run.py`.

- **The board**: all 100 features as cards — id, title, area, size, `parallel`, dependencies,
  state. Filters by area and by state; a search field.
- **One feature**: open the card, read the rendered spec, press **Build**.
- **Ten features**: select or paste ids, press **Queue**. The scheduler runs them in dependency
  order, one exclusive feature at a time, bounded by a work-in-progress limit.
- **Live build**: one row per build — current step, elapsed, tokens, checks, gate verdict, PR
  link, kill switch. Updates by server-sent events, with a no-JavaScript fallback on reload.
- **Never on the page**: a credential, a raw prompt, a full diff of sensitive paths. Counts and
  identifiers only.

The board is generated from `features/MANIFEST.json`, so a spec change appears without a code
change.

## 3. Queue and scheduler

- **State machine**: `proposed → queued → dispatched → built → gated → pr_open → approved →
  merged`, plus `held`, `failed`, `cancelled`. Every transition is timestamped and audited.
- **Storage**: SQLite under `demo/.local/factory/` (gitignored), one table for features, one for
  runway events. No new service.
- **Scheduling**: a single tick, an advisory lock, a WIP limit, and an exclusivity rule for a
  feature marked `parallel: false`. Dependencies are read from the manifest and re-checked at
  dispatch; a missing dependency holds the item instead of skipping it.
- **Kill switch**: stops dispatch, leaves the queue intact, marks the running build `held`. It is
  the same switch the demo already exposes.

## 4. Dispatch

A dispatched feature becomes one Flue run with a frozen brief:

1. the feature file, rendered, as the task;
2. the acceptance list as the definition of done;
3. the tier the feature declares (tier 2 for file edits, tier 3 for a shell or an install);
4. a tool surface bounded to the app's own tree;
5. a hard time limit and a step cap.

The run reports back: changed paths, checks it ran, a short summary, and the usage it consumed.
The runner writes one branch, one commit series and one draft pull request. All model calls go
through the relay; the sandbox never holds the provider key.

**Dry-run is the default.** A build can run end to end with stub inference — same queue, same
state machine, same gate, same PR shape against a scratch repository — and prove the factory
without spending a token. A live run is an explicit switch per build, and the cockpit shows which
mode produced a row.

## 5. Gates

The gate runs on the built tree, in a fresh sandbox, never in the workspace that produced it:

- the app's own suite, `tools/factory-tests`, `knowledge-check`, `doc-links`, `repo-health`;
- the feature's acceptance list, one line per check where it is mechanical;
- a verdict object: pass or fail, per-check status, duration, artifact digest, trace link.

A failing gate returns the feature to `failed` with the check named. No automatic retry loop: two
failures become an issue.

## 6. Merge policy

This is the boundary that keeps autonomy from becoming unbounded privilege.

- **No direct push to `main`, ever** — including by this AI. `main` receives release pull requests
  only.
- A builder pushes a branch and opens a pull request into `develop`.
- **Auto-merge is allowed only when all of these hold**: green gate, recorded review, and every
  changed path inside the allowlist (`demo/app/**`, `demo/tests/**`, `demo/flue/**` except the
  observer, `docs/**`, and the app's own tests and docs).
- **Never auto-merged, whatever the verdict**: `.github/`, `demo/app/security*`, the collector
  config, migrations, `demo/compose.yaml`, deploy files, `tools/`, anything touching secrets,
  branch protection or the relay. Those wait for the owner, always.
- Every merge records: feature id, gate verdict, reviewer, commit sha, trace id.

## 7. The observer agent

One Flue agent watches the queue and the traces and does three things: triage a failure into an
issue (deduplicated against an open one), propose a pull request when a build is green but stuck,
and report to the owner in one message per day.

It may open issues, comment with evidence, and open pull requests. It may not merge outside the
allowlist, change branch protection, edit CI, rotate a secret, or touch the deploy files. Its token
is scoped to issues and pull requests. Its runs are audited like any other, and the kill switch
stops it too.

## 8. Security of the factory itself

- Loopback only, administrator session, CSRF token on every action, rate-limited.
- No secret in the page, ever; the relay key stays on the host and never reaches a child.
- The brief given to a builder is the feature file plus the acceptance list — never a transcript,
  never a previous run's output.
- A build's output is untrusted: it is reviewed by the gate, not merged because it says it passed.
- The dry-run path exercises the same code as the live path, so the demonstration is not a veneer.

## 9. Build order — what this session actually ships

| Slice | Content | Proof |
| --- | --- | --- |
| S1 | board, queue, state machine, dry-run worker, live view, kill switch | queue ten features, watch them run dry, every transition audited |
| S2 | real dispatch to Flue, branch and PR against a scratch repository | one feature becomes a green pull request, unattended |
| S3 | gate verdict, allowlist merge, observer agent | three diffs (allowed, outside, mixed) behave as §6 says |
| S4 | VPS override and the restore drill | runbook ends on a healthy ready endpoint over HTTPS |

S1 is what the owner can open and click tomorrow morning; S2 is the first live build.

## 10. Review checklist

1. Can a build touch anything outside the app tree or the allowlist?
2. Is there a path where a green verdict is not required before a merge?
3. Does the dry run use the same state machine, gate and PR shape as the live path?
4. Can the observer agent escalate its own privileges, directly or through a pull request?
5. Does the front leak a secret, a prompt or a diff of a sensitive path?
