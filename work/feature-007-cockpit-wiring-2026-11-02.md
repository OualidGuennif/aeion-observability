# Feature 007 operator wiring — 2026-11-02

Owner instruction: connect execution so new product features can be launched from the cockpit.
The smallest useful next target is 007 (content sanitization), depending only on the verified
001 baseline. The separate canonical product stays untouched until a real build is launched
and its result is integrated. No new service, dependency or orchestration layer is added.

## What changed

- Target `forum-app-007.json` pins product `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`, with
  its own adapted brief and independent Java contract. Existing JSON clients retain the body
  field; safe body_html is derived from canonical normalized text. No migration is required.
- The old author input contained only a brief. Optional explicit context_files now supplies
  the complete relevant main Java files from the exact Git commit, so the author sees the
  interfaces it must preserve. Dirty host files, configuration paths and symlinks cannot enter
  this context. It is limited to 8 files, 24000 bytes/file and 48000 labeled UTF-8 bytes total.
- Oversized briefs are refused at loading and before transport, replacing silent truncation.
  Context lives outside candidate write scopes. It is not copied into default telemetry.
- The existing generic per-feature resolver/worker remains the execution path; 013 and 017
  stay locked, and unsupported targets stay blocked. No fake baseline unlocks prerequisites.

## Contract qualification

The protected contract SHA-256 is
`c77e99036530853a9e933731f94d930304c2cab88eb0772e06d1004e2e0f273a`.
It verifies 30 XSS/remote-resource payloads with a parser that allows only the defined elements
and no attributes, exact Markdown/normalization/code-block fixtures, stored canonical text,
create/read/list output, codepoint bounds including supplementary Unicode, and HTTP 413 without
an extra outbox row. Authentication, CSRF and existing business refusals remain covered by the
full existing Java suite.

The real baseline ran all 59 Java cases and failed exactly the five new contract tests:
missing sanitizer/body_html/normalization and the old 400 refusal instead of the new 413.
No compilation error concealed the negative result. A disposable injected candidate then
passed **59/59**, including the unchanged contract (41565 ms protected check).

That candidate traversed the actual FactoryApp catalog/CSRF queue API, dispatcher, LiveBuilder
prompt construction with pinned context, artifact/scope review, isolated Gradle check, two
synthetic distinct-family review votes, fake publication, and terminal `simulated_complete`.
The complete changed-file review was 17078 characters, within 24000. All state and fake budget
records were in a temporary directory. Neither model votes nor author bytes are represented
as real provider evidence; no provider call ran and no real product feature was marked done.

Isolation: image
`sha256:93b8a14ea2f412782e4e842651273b4d903e35cc496284f178fbbe2d67d00976`,
network denied, non-root, read-only root/toolchain/cache, no host environment or Docker socket,
3 GiB memory, 2 CPUs and 512 PIDs. The external contract remained outside candidate control.

## Operator activation and remaining limits

Controller reloaded as PID 40317 after an atomic no-active-build preflight and a separate
no-running-lab/campaign check. Root returned HTTP 200. Persisted availability readback is
`007: {state: ready, selectable: true, reason: null, missing_dependencies: []}`; configured
targets are 007/013/017, and 001/013/017 remain locked. Build row count and budget ledger SHA-256
are unchanged. No queue entry or model call was created in the real state. Evidence:
`/private/tmp/aeion-cockpit-ui-work/007-activation.json`.

Targeted checks pass: 174 Python cases (including 11 source-context and 2 local 007 profile/API
cases), 7 client cases, knowledge-check (0 problems), doc-links (108 links), repo-health,
whitespace and 53-file snapshot drift checks. The automated approval service initially refused
the full-suite command because of its usage limit, without judging it unsafe. Subsequent
controller reload and full-suite execution were approved normally; no approval bypass was used.

Complete regression on a public-source snapshot with empty local state: 557 demo cases, exit 0
(550 passed, 7 local-checkout skips). Those 7 profile cases passed separately in the real local
checkout as part of the 174-case targeted run. Examples: 33 passed. Flue: 14 passed. Client:
7 passed. Logs: `/var/folders/71/5ylk1yz559s8pdrf5r4t71sw0000gn/T/aeion-full-pass-20261102-ghpp42x2`.

Manual boundary review covered profile paths, pinned Git reads, symlink/blob/type/size refusals,
context placement, provider input bounds, candidate write scopes and metadata-only telemetry.
No external scanner or real model review was invoked for this controller change. No context
source, session material, prompt or provider payload is logged as qualification evidence.

Operator steps: refresh `http://127.0.0.1:8088/`, sign in again if requested, keep the Ready
filter, select **007 — Content sanitization for user text**, then click **Build selected**.
The real outcome appears under Build activity with its check/review/trace evidence.

The next real action is an owner launch of 007 in Ready. This is a new model implementation,
not deployment of the injected qualification candidate. A real model can still fail or be held;
checks, review and budgets decide the recorded outcome. Automatic product integration and
runtime rollout are separate from authoring. The other 96 catalog entries are not falsely
advertised as executable, and the advanced Flue/OpenShell lab is independent of this Docker
check path. Authenticated browser acceptance is not claimed while its connector is unavailable.

Local raw qualification evidence and the explicitly synthetic candidate helper are under
`/private/tmp/aeion-cockpit-ui-work/007-before.json`, `007-after.json` and `qualify_007.py`.
The existing product snapshot and canonical product working tree remain unchanged.
