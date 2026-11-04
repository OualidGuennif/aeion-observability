# Code pass and one real feature — 2026-11-02

Follow-up: the owner authorized direct implementation after this assessment. Feature 017 and
the actionable controller defects are now repaired; the verified commit, trace, completion lock
and current limits are in [the repair record](feature-017-codex-repair-2026-11-02.md). The attempt
results below retain the original failed evidence.

Owner instruction: review the code, launch a feature and monitor its actual outcome. This
authorizes the local paid feature-017 workflow and its independent reviews under the existing
two daily purses. It does not authorize a remote push, merge, release or deployment.

## Scope and evidence

Controller revision: `786e3ff47f26fa960c2c705de18f9d2d07155457` plus the working cockpit/target
changes. Reviewed the root/Factory routes and client, administrator/CSRF boundary, target and
artifact validation, admission/claim/cancellation/recovery, live author/client, independent
review circuit, isolated Java check, daily accounting, telemetry/readback and the legacy CLI.
Preserved concurrent Factory updates and the separate product checkout.

This is a local code and integration assessment, not an external security certification or a
line-by-line audit of every vendored dependency. No secrets, environment dumps or raw model
transcripts were inspected. The existing trusted controller loads its own credentials normally.

## Confirmed defects corrected

1. Two independent Store instances could claim the same queued job. A deterministic interleaved
   test returned two different attempts for one build. Claim now acquires `BEGIN IMMEDIATE`
   before reading its preconditions; baseline, completion, hold, cancellation and recovery use
   the same transaction boundary.
2. A completion could overwrite a concurrent cancellation after reading stale state. The
   interleaved regression reproduced this and now proves that final transitions serialize.
3. The default 60-second lease was shorter than a protected check's 900-second deadline.
   Dispatch now reserves a lease covering the longest check, one bounded author call, two
   bounded review calls and 60 seconds for teardown. A lease is a recovery window, not a promise
   that an arbitrary Git subprocess cannot hang.
4. Restarting an expired attempt reset it to queued, allowing another paid call with uncertain
   prior effects. It now holds as `reconciliation_needed`, preserving attempt identity. Held
   work blocks a new launch until the operator inspects it and explicitly cancels it.
5. Hold transitions discarded attempt identity and review-circuit refusals were not recorded
   with the artifact. Holds retain identity and may persist bounded trusted evidence; circuit
   holds now retain gate/review/coverage and their telemetry result.
6. Malformed feature IDs or a non-string idempotency key could escape as TypeError/SQL errors.
   The API/store now reject those values before mutation, with HTTP 400.
7. The first real authoring call timed out before producing code. Its 60-second transport window
   was identical to a short review's. The author now uses 180 seconds; reviews retain 60 seconds.
   An injected transport regression proves both actual timeout arguments. No retry is automatic.
8. Builder errors had no factory trace. They now emit bounded failure telemetry and preserve only
   the exception type plus controlled application error codes, never arbitrary exception text.

The new recovery tests failed before correction (four behavioral failures and the missing
evidence argument). The malformed-admission test also reproduced the original TypeError, and
the author timeout regression failed before the new transport argument was wired.

## Validation

- Final sanitized source snapshot:
  `/private/var/folders/71/5ylk1yz559s8pdrf5r4t71sw0000gn/T/aeion-full-pass-20261102-5_8qbybd`.
- Demo: 535 tests discovered, 530 passed, 5 local-product skips, exit 0, 30.810 seconds. The five
  `test_forum_target_profile.py` cases passed separately against the actual checkout.
- Examples: 33 passed; Flue: 14 passed; cockpit client: 6 passed.
- `tools/factory-tests`: PASS, including hook/context/connector/architecture/eval/loop checks.
- Targeted live-client tests: 25 passed; feature-target tests: 7 passed; recovery tests: 5 passed.
- Knowledge/doc-link/repository-health and whitespace checks are recorded in the final task
  validation entry. No new dependency, service or privilege was added.

## Actual feature execution

Product: `OualidGuennif/aeion-autonomous-forum`, clean canonical checkout at
`b0201db86135b943e84e9fececbde87dbaa7d36e`. The 017 contract is independently injected by the
trusted checker and previously failed the unmodified base at the missing validation assertions.
The preflight found no queued/dispatched job and no prior 017 build. The Docker probe qualified
image `sha256:93b8a14ea2f412782e4e842651273b4d903e35cc496284f178fbbe2d67d00976` with denied
network, non-root execution, no host environment/socket and bounded resources.

The owner's browser was logged out. Admission therefore used the existing Store operator API
locally, without reading an administrator token or changing HTTP authentication. The running
controller picked the job up through its normal FactoryApp/DispatchWorker path. The fixed request
key prevents accidental replay of the operator command from launching another attempt.

First request: `c4c67c272ac748a99e39f26513503034`, attempt
`94a3de22e804417085f134761c0064c9`, author `glm-5.3-flash`.
Outcome: failed with `builder_error/TimeoutError`, no generated file, no protected check/review,
no publication. Langfuse readback confirmed trace `f5f44fd55f2833bfa38b124a27c9b367`, observation
`b04641fd83953711`. Unknown provider usage keeps its $0.50 reservation open.

After the tested timeout correction, one controlled retry was admitted:
`af511eaca2b1496b8d6303db74731a3a`, attempt `88dccfe2ad4347e1b50c16aa0e07305b`.
It produced a 5,252-byte Java filter. The isolated protected check failed compilation in 14,992 ms,
before any JUnit assertion or review. A second offline protected run reproduced it in 11,774 ms:
`RequestValidationFilter.java:82`, unresolved enum constant `UNPROCESSABLE_ENTITY`. No production
code was changed by the operator to make this pass. The source artifact is preserved under its
original build; digest `de175cf72e2db4576d1ad62611ecf3ce78f3854c3d1d1437bef6332d96e6d816`.
Langfuse confirmed trace `a11f280923869e0807443344c8d7a5ca`, observation `673132be43c7af72`.

The trusted brief now names the actual package and the verified API constraint (numeric 422,
no unsupported enum or unused resource-info injection). A final targeted attempt was explicitly
admitted: `87655cb326db471d86d34bba92393851`, attempt `460bae9048b64db2adc5bafa9e8e8f7d`.
Final outcome: **failed protected acceptance**, compilation succeeded. Gradle ran in 40,452 ms;
the external contract failed two tests and the candidate's own test class failed four. A request
with an unknown registration key returned 201 instead of 422; a missing/wrong-type field returned
400 instead of 422. The candidate's login cases returned 401 instead of 422. This happened in the
disposable test database, not against the running forum or real accounts.

Confirmed cause: `REQUIRED_FIELDS` stores `/api/...` keys, while `normalize` strips the leading
slash. Every lookup returns null, so the filter returns before validation. The source is in the
isolated build's `demo/forum-app/src/main/java/local/aeion/forum/http/StrictRequestValidationFilter.java`
(map near line 37, lookup near line 50, normalizer at line 136). No manual product patch was
applied. Artifact digest: `06374139b7ce1662b63f4a9af3b0be7d032ae38ea86ead9f89c62164f5cab987`.
Langfuse confirmed trace `9aa21fadcf879d124bbff0d05462c3ca`, observation `96684ccdbd760211`.

The generated implementation plus its own tests also produce a 7,655-character complete review
input against the existing 6,000-character envelope. A pure local `_review_input` check confirms
that it would hold before reviewer spending even if acceptance passed. This is not a successful
model review. The trusted brief now names both the route-normalization defect and the envelope;
the next implementation should be focused and avoid duplicating the injected contract.

Three real authoring attempts, zero reviewer calls, zero publish/integration/deploy actions. The
original timeout retains one unknown-usage $0.50 reservation; the other two have provider-reported
settlements. Final forum purse: $1.00 counted including prior work and unresolved reservations,
$14.00 remaining. These are journal/provider amounts, not a billing invoice. No queued/dispatched
job remains; the canonical product checkout stays clean at its original commit. No further paid
attempt was launched after the third failure.

## Limits and follow-up

- Only 017 is configured as the next unmet feature; 97 catalog entries still require real
  contracts/bases/prerequisites. Completed 001/013 remain locked.
- Checked candidates are separate from incorporated product changes. No automatic integration
  or remote publication occurred.
- Model selection is a deterministic heuristic over declared quality/cost priors and bounded
  in-memory review outcomes. It is not a learned, persisted benchmark of product coding quality;
  expired DeepSeek remains excluded. A successful transport does not prove good code.
- `run_features.py --live` is a legacy simulated-author/review-only staging path, not the live
  Java authoring path. Its current docstring describes simulation, but its name remains easy to
  misread. Use FactoryApp/DispatchWorker for real implementation; unifying that legacy CLI is a
  separate change, not a reason to start another frontend or orchestration service.
- Authenticated cockpit/Langfuse browser acceptance remains unavailable while the owner is
  logged out. Backend trace confirmation is readback evidence, not a browser screenshot.
- The official [Langfuse trace URL guide](https://langfuse.com/docs/observability/features/url)
  describes project-scoped links. The current short `/trace/<id>` link reaches the local sign-in
  redirect; its post-login resolution was not verified and is not claimed as a confirmed defect.
- The protected check records bounded test names, but a compilation failure currently has an
  empty failed_tests list. A diagnostic replay was needed to identify the unsupported symbol.
  Future work should expose sanitized compiler categories/identifiers rather than raw output.
- The live author receives an adapted brief rather than repository-reading tools or an iterative
  repair loop. Exact interface constraints belong in that brief; successful single-call generation
  must not be confused with a general coding-agent implementation capability.

Next concrete implementation task: have the builder repair route normalization, keep the exact
body/type/field refusal contract, and return a small candidate that fits complete review. Run the
independent protected acceptance before any two-family review. Do not integrate a failed artifact,
disable the test or expand permissions to turn this result green.

Sensitive-boundary review: caller-controlled IDs cannot select commands/repos/scopes; trusted
target validation and candidate/feature equality remain; generated code executes only in the
qualified disposable check boundary; complete review coverage, distinct reviewer families,
separate daily purses and unknown-cost liabilities remain. No native external security scanner
or independent model audit was run as part of this code assessment.
