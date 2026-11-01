# Trust model — what a rogue agent can and cannot do

Written after the owner asked what happens if the language model behind an agent "goes rogue and
wants to destroy everything". The answer is a list of properties, each tied to the code that
enforces it. Where a property is not enforced, it says so.

## The one-line rule

**The model produces data, never authority.** It can propose a diff; it cannot run code on the
host, cannot publish, cannot merge, cannot widen its own scope, and cannot judge its own work.

## 1. Generated code never runs on the host

- All execution is inside OpenShell: `landlock=hard_requirement`, dedicated UID (10001), no
  network (`NetworkMode=none`), no Docker socket, read-only image paths.
- The host process only reads files and compares digests. `digest()` refuses symlinks, devices
  and anything over 32 KiB before it looks at the content.
- The acceptance checker runs in a **fresh** sandbox (`role="check"`) where no agent process has
  ever existed, and reads the artifact seeded into that sandbox — never the agent's workspace.

## 2. The diff is validated as data, not as a claim

`demo/factory/artifact.py` enumerates the real Git diff and rejects, as a whole:

- any path outside the frozen literal write scopes;
- absolute paths, `..`, backslashes, `.git` metadata, symlinks, non-regular files;
- renames where either endpoint escapes scope.

A mixed diff is rejected entirely — there is no partial accept that could smuggle one bad file.

## 3. The transport moves bytes; it does not grant execution

`collect()` reads a sandbox directory over the exec channel and `materialize()` writes those bytes
on the host, refusing absolute paths, `..` and backslashes, skipping unchanged files, and failing
closed (`SANDBOX_SYNC_TARGET_LOCKED`) when a file cannot be replaced. Copying a file is not
running it.

## 4. The judge is not the candidate

`demo/factory/checks.py` runs the protected checks the **host** chose, from a registry the
candidate cannot reach. A required check that is missing yields `qualification_missing`, never a
green result.

## 5. The reviewer is rules, not another model

This is the direct answer to "un autre agent reviewer analysera". **A second LLM would be
untrusted input too** — a rogue reviewer approves a rogue diff. So `demo/factory/review.py` is a
deterministic rule engine over the bounded diff:

| Finding | Decision |
| --- | --- |
| path outside the accepted diff, empty diff, rejected artifact | **refused** |
| credential-shaped string (`ghp_`, `sk-`, `AKIA`, private key header, Slack token) | held |
| `rm -rf /`, `curl … \| sh`, `chmod 777`, `sudo`, `git push --force`, `npm publish` | held |
| dependency manifest change (`package.json`, lockfiles, `requirements.txt`, …) | held |
| binary content, file > 256 KiB, > 50 files, diff > 512 KiB | held |

Same input → same verdict and same `digest` (content-addressed, so a different diff can never
reuse an approval). Holds go to `owner_review_required`; the reviewer can never publish, and its
verdict is bound into the receipt.

## 6. The build agent stops on its own branch

`demo/factory/boundary.py` is the written contract every build agent receives, and the coder
system prompt in `demo/flue/src/agents/coder.ts` carries the same five rules (`test_factory_boundary.py`
fails when the two copies drift):

1. work only inside the workspace and the declared write scope;
2. commit to your own branch only — push nothing, open no pull request, merge nothing;
3. never review your own work;
4. stop when the checks pass or when you cannot continue, and say why in `HANDOVER.md`;
5. do not wait for a reviewer, do not poll for one, never merge on anyone's behalf.

The brief is written to `TASK.md` outside the clone, so it can never become part of the artifact.
Stopping is then *enforced*: the freeze digest pins the branch contents, the publisher re-verifies
that digest before pushing, and a commit after the freeze invalidates the receipt. An agent that
ignored the instruction would produce a request the publisher refuses.

## 7. Two other model families must agree

`demo/factory/review_circuit.py` is the answer to "the agent that codes must not cast the first
review vote, and the second vote must not come from either of the first two models":

- the author model **and its family** are excluded from the draw;
- vote 1 comes from a second family, vote 2 from a third — `models.py` enforces distinct families,
  not just distinct names;
- any reject, any transport error and any malformed answer yields `held`; there is no retry that
  turns a failure into an approval;
- the prompt is hard-capped at 6000 characters and the answer at 120 tokens, and the answer is
  parsed as data (fenced JSON), never executed;
- the votes and their digests are bound into the receipt.

`demo/factory/publisher.py::verified_receipt` refuses a receipt whose gate is not passed, whose
review is not approved, whose circuit is missing, unapproved or carries fewer than two votes, or
whose artifact or base digest differs from the queued request.

## 8. Publishing is a separate, narrow authority

`demo/factory/publish.py` refuses a forged issuer, a target repo other than the pinned one, a
cancelled build, a forged artifact digest, and any path outside the write scopes. It **holds**
when no approved review is attached, when the base or head moved, or when the path is sensitive
(`auth`, `migrations`, `security`, `moderation`, `rules`, `runtime`, `deploy`, `permission`, any
dependency file). The real forge is dry-run by default; merging needs `allow_merge` **and**
`merge`; a stale or uncertain result is reconciled, never re-published.

The worker never holds the publish key: it writes a request to `demo/factory/queue.py` and exits.
`demo/factory/publisher.py` is the only process that loads `GH_API_KEY`, and it proves at start-up
that no inference and no release credential is present. One key per capability:

| Key | Role | GitHub permissions | Can it merge `main`? |
| --- | --- | --- | --- |
| `GH_BUILD_KEY` | build | `contents:read`, `pull_requests:read` | no |
| `GH_API_KEY` | publish | `contents:write`, `pull_requests:write` | no — and it belongs to a process that never reviews |
| `GH_RELEASE_KEY` | release | `contents:write`, `pull_requests:write` | yes, and only a human holds it |
| `OPENCODE_API_KEY` | inference | none | no |

`keys.py` owns the table, `assert_only()` refuses a role the process does not need,
`assert_worker_isolated()` refuses publish or release keys next to a worker, and
`demo/app/settings.py` scrubs every publish-class key at start-up. The root `.env.example` states
the same contract for the owner, and `test_factory_keys.py` fails when the two drift.

Branch protection is the second lock, independent of every process above: `main` and `develop`
require a pull request, a green required check (`Knowledge, links and repository health`,
`Product artifacts`, `secret-scan`, `dependency-scan`, `sast-scan`), linear history and resolved
conversations, with force-pushes and deletions refused and admins included. A probe push was
rejected on both branches on 2026-11-01.

## 9. Everything is bounded

Diff ≤ 512 KiB, ≤ 50 files, ≤ 256 KiB per file; bridge operations ≤ 1 MiB; sync ≤ 8 MiB; audit
attributes are an allowlist of short scalars (free-form text is rejected — the audit layer raises
`INVALID_AUDIT_EVENT` rather than storing it); no prompt, body or provider text is logged.

## 10. Where the human stays

- Sensitive paths, dependency manifests, credential-shaped content.
- Any merge, any release, any deployment.
- The pull request itself is the human boundary: the agent's branch is isolated, and nothing
  reaches `main` except through a reviewed PR.

## What is *not* guaranteed

Rules catch known-bad shapes, not semantics. A rogue model can still write malicious *code* that
no rule flags. The design does not pretend otherwise: that is exactly why nothing is auto-merged,
why the diff is bounded and content-addressed, and why the final decision is a human reviewing a
pull request on a branch. Claiming "the reviewer makes agent output safe" would be false; the
claim is "no agent output can reach `main` without a human, and every automated stage fails
closed".
