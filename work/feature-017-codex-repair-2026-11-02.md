# Direct implementation of the code-pass report — 2026-11-02

Owner instruction: implement the report directly, without delegating the repair to DeepSeek.
This explicitly supersedes the earlier delegation-only preference for feature 017. Delivery is
local code/controller state, with no paid author call, remote push or remote deployment.

## Product implementation

Canonical repository: `demo/.local/factory/agents/aeion-autonomous-forum`.
Local `develop` commit: `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb` (clean working tree).
The read-only 53-file product snapshot in this repository is unchanged; its drift check passes.

RequestValidationFilter bounds entity reads to 16385 bytes, restores accepted bytes, uses the
same route normalization as its rule keys, and validates JSON token types before endpoint map
coercion. It rejects malformed/non-object JSON, duplicate keys, trailing tokens and unknown,
missing or non-string fields. Error bodies contain sorted unique field paths, not values.
The existing business refusals, cookies, CSRF, response headers and unsupported media types stay
covered by the full product regression suite. No dependency/build-file/schema change.

Six new product HTTP tests plus the unchanged external contract ran in the qualified denied-
network Docker boundary. Before the filter: 58 tests, 6 failures. Final implementation: 58 tests,
0 failures/errors/skips in 41683 ms. The exact committed base passed again in 40892 ms, then a
re-verification passed in 38069 ms. The contract SHA-256 stayed
`60c2ff0fd1b003f9774d431f0be74f6cb3f4a2df8f9e5772b5d216e901faba7d`.

The normal early filter runs before the existing CSRF guard and resource-owned authentication.
The [Quarkus REST guide](https://quarkus.io/guides/rest/) documents why a pre-matching stream
reader is unsuitable for the event-loop phase; an initial prototype was rejected before delivery.

## Controller repairs

- Compilation failures now expose bounded Java file/line/symbol identifiers and a failure
  category. No source line, exception dump or arbitrary compiler prose is put on the board.
  The client renders these and failed-test identifiers with HTML escaping.
- The complete review envelope is 24000 characters, enough for the observed Java patch with
  tests. Larger inputs still hold before any vote; both independent families see every byte.
  No excerpt-based approval or permission expansion was added. The author prompt uses the same
  limit instead of leaving it implicit.
- `run_features.py --live` now fails before state creation or model work. The legacy deterministic
  staging fixture defaults to separate state; the existing cockpit remains the real build path.
- Docker path translation preserves alias spellings such as macOS `/var` versus `/private/var`
  before mounting the resolved workspace. The regression failed before the one-line correction.
- Feature-017 baseline verification requires its own target and the independently injected
  contract. A broad successful Gradle invocation alone cannot mark it implemented.
- Baseline receipts now retain proof, build/feature identity and best-effort trace metadata.
  Re-verification ignores fresh timestamps/duration for idempotency, preserves old receipt formats,
  refuses changed proof, and cannot supersede an active/held request for the same feature.
- The direct baseline CLI no longer lets factory/queue.py shadow Python's queue module, which
  had broken the exporter on missing LifoQueue. The regression reproduced that exact failure.
  A replay retries an unavailable trace without duplicating the implementation record.
- Trace links use the documented project route and the existing aeion-demo project initialized
  by Compose ([Langfuse trace URLs](https://langfuse.com/docs/observability/features/url)).

The new compiler, review-size, legacy-CLI, alias, baseline-proof and CLI-bootstrap regressions
failed before their fixes and pass after. No independent model approval was fabricated for the
Codex-authored change; this is owner-authorized local implementation with independent deterministic
acceptance and a local sensitive-boundary assessment. Generated builds retain their two-vote gate.

## Persisted outcome and observation

Verified baseline build: `2716fe2bb1044ceabdecdcc6f4e38513`.
Exact base: `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`.
The baseline was first recorded, then replayed with the same ID during trace recovery.
Langfuse readback confirmed trace `18fe0c7e99f4af1cb8d78278cf42d7f9`, observation
`9951e9bf4653582e`, session `factory:2716fe2bb1044ceabdecdcc6f4e38513`.
Only identity, hashes and outcomes were exported; no code, prompts, tool content or secrets.

Actual local availability is implemented/selectable=false for 017. A new-key admission probe
was refused as feature_already_completed:017, and the number of 017 records stayed unchanged.
Completed/locked IDs are 001, 013 and 017. No queued/dispatched job remains. The prior three
failed attempts and the initial unknown-usage reservation were retained, not relabeled or erased.
Both budget summaries remain $1.00 counted / $14.00 available; no paid model call ran in this repair.

## Final validation

- Demo Python suite: 544 discovered, 539 passed, 5 checkout-specific skips, exit 0 in 31.181 s.
  Those five profile cases passed separately against the actual checkout.
- Examples: 33 passed; Flue: 14 passed; client: 7 passed; node syntax check passed.
- Final public-source snapshot:
  `/private/var/folders/71/5ylk1yz559s8pdrf5r4t71sw0000gn/T/aeion-full-pass-20261102-z64ew5n0`.
- Product knowledge, doc-links for the repair delta against its previous HEAD (99 links), health
  and whitespace checks pass. Two missing existing Pi RPC source references were repaired.
  Historical origin/develop-relative L3 documentation drift from older Factory upgrades is
  separate from this repair and is not certified by that scoped check.
- Controller knowledge, doc-links, health, whitespace and snapshot drift checks pass.
- Browser control could list the existing cockpit tab but could not attach to it (provider
  capability unavailable). No browser credentials were read and no authenticated visual acceptance
  is claimed. Client behavior has deterministic DOM-free regressions; backend state is real.

## Scope limits

The running forum container was not rebuilt/replaced; the implementation is committed in the
canonical product and verified in disposable Docker runs. A code baseline is not a deployment.
The controller reload is separate from forum publication and preserves the persistent state.
The other 97 catalog contracts and task-quality model benchmarking remain separate work;
no claim that all 100 features can run, that heuristics are trained routing, or that this is an
external security certification. No new service, dependency, queue or agent orchestration.

Subsequent owner-authorized operation: the [clean local restart](clean-restart-2026-11-02.md)
rebuilt and replaced the forum runtime from this exact commit, then verified its HTTP behavior.
The paragraph above records the earlier code-repair boundary, before that separate restart.
