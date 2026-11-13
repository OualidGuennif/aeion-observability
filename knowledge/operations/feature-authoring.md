---
type: Runbook
title: "Authoring factory-compatible features"
description: "Canonical rules and battle-tested lessons for writing Agora features so preparation, negative control, OpenShell builds, and independent review succeed cleanly."
status: stable
review_after: 2027-02-13
sources:
  - resource: ../../demo/forum/PLAN.md
    title: "Agora product contract and catalog rules"
  - resource: ../../demo/forum/ARCHITECTURE.md
    title: "Approved Quarkus, PostgreSQL, and React architecture"
  - resource: ../../demo/forum/tools/generate_features.py
    title: "Catalog validator and Markdown renderer"
  - resource: ../../demo/factory/preparation.py
    title: "Task freezing, baseline negative-control retries, and preparation guards"
  - resource: ../../demo/factory/product_checks.py
    title: "Product acceptance prompt, registered transitions, and Docker check runner"
  - resource: ../../demo/factory/product_harness.py
    title: "Isolated JUnit harness oracle for Feature 003"
  - resource: ../../demo/factory/store.py
    title: "Preparation evidence validation and admission state machine"
  - resource: ../../demo/factory/flue_builder.py
    title: "Author context limits, handover check propagation, and candidate recovery"
  - resource: ../../demo/app/sandbox.py
    title: "OpenShell sandbox isolation and provisioning retries"
  - resource: ../../demo/flue/src/tools/factory-checks.ts
    title: "Protected check state and passed-check completion guidance"
---

# Authoring factory-compatible features

[Operations index](index.md) · [Flue factory execution](../components/factory-flue.md) · [Factory architecture](../components/factory-architecture.md) · [Specs first](../policies/specs-first.md)

Every feature run goes through four deterministic gates before merge: **catalog freeze**, **independent preparation + baseline negative control**, **OpenShell tier-3 authoring (`run_protected_checks`)**, and **two-vote independent review**. Features designed without those four gates in mind fail cleanly (fail-closed) rather than passing silently.

## 1. Where features live and how they freeze

1. **Edit Python specs, never generated Markdown.** Canonical definitions live in `demo/forum/tools/specs_a.py` through `specs_f.py`. After any edit, regenerate `demo/forum/features/` and `MANIFEST.json` and verify there is zero drift:
   ```bash
   python3 -B demo/forum/tools/generate_features.py
   python3 -B demo/forum/tools/generate_features.py --check
   python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
   ```
2. **Satisfy static catalog and `freeze_task()` invariants:**
   - Stable numeric ID (`001`..`100`), unique title slug, `tier: 3`, valid `area` and `size` (`S`, `M`, `L`).
   - `phase` in `P0`..`P5` with acyclic `depends_on` referencing only features in the same or an earlier phase.
   - Between `2` and `4` concrete delivery steps (`<= 220` characters each) and all mandatory spec sections (`goal`, `scope`, `delivery`, `security`, `accept` with `- [ ] ` items, `test`, `out`).
   - `write_paths` are literal relative paths (no globs, `.` or `..`) inside `demo/forum-app/`, `demo/forum-web/`, `demo/forum-docs/`, or `knowledge/components/`. Regular Java tasks are narrowed by `preparation.py` to Java main/test/resources, `test/resources/`, `demo/forum-web/`, `demo/forum-docs/`, and `knowledge/components/`; Gradle/npm dependency changes require explicit transition adapters.
   - `parallel: true` specs must have strictly disjoint `write_paths` and cannot reserve full product roots.
   - Markdown byte size must stay `<= 12,000` bytes ( regular non-symlink UTF-8 file), matching both `catalog_digest` and `architecture_digest`.
   - Superseded stack names (`FastAPI`, `pytest`, `extra=forbid`, `no client framework`, `without JavaScript`) are rejected at generation time.

## 2. Design acceptance observability upfront (avoiding `preparation_negative_control_missing`)

Before an author starts, `TaskPreparer.prepare()` executes the frozen `acceptance.mjs` contract against the **untouched product baseline (`origin/main`)**. If all assertions pass on baseline, preparation is refused (`preparation_negative_control_missing`).

| Feature kind | How the factory verifies it | Authoring rule |
| --- | --- | --- |
| **User-facing / API / Web (`004`+)** | LLM preparer writes Node 26 / `fetch` / Playwright 1.64.1 black-box tests against `http://127.0.0.1:8080`. It has **no** Java classes, DB credentials, shell, or host files. | Specify at least one concrete **externally observable HTTP or browser delta** (route, status code, JSON shape, DOM state, auth/CSRF refusal) that **does not already exist** on baseline. |
| **Pure internal transition / SPI / build seed (`001`, `002`, `003`, `014`)** | Registered static contract in `demo/factory/transitions/<kind>/` plus supervisor-owned oracle (`product_checks.py`, `product_harness.py`). | Do **not** leave a pure internal/JUnit feature on LLM HTTP preparation if all HTTP probes already pass on baseline. Register a supervisor oracle + transition files and add the ID across `product_checks.py`, `preparation.py`, `store.py`, and `flue_qualification.py`. |

Although `TaskPreparer.prepare()` retries baseline-passing contracts across up to `3` distinct model families with diagnostic feedback (`_baseline_retry_note`), unambiguous observable deltas prevent wasting preparation attempts altogether.

## 3. Battle-tested lessons from the factory (preventing deadlocks and hallucinations)

Every rule below comes directly from production incidents resolved in Features `001`–`003`:

1. **Never contradict inherited transport and security guards:**
   - **16 KiB HTTP body limit:** Quarkus HTTP transport rejects payloads `> 16 KiB` with `HTTP 413` before application validators run. Do not write acceptance requirements expecting `400` or `422` on `20 KiB` payloads; `acceptance_prompt` enforces `413` above `16 KiB` and `422` (`{"error": "validation_failed", "fields": [...]}`) or `400` on bounded invalid JSON.
   - **CSRF on cookie mutations:** Committed endpoints enforce `X-CSRF-Token` (returned as `"csrf"` by `/api/auth/login`) on authenticated `POST`/`PUT`/`DELETE` requests carrying session cookies. Any authenticated mutation spec or example must preserve CSRF protection.
2. **Separate internal test fixtures from live HTTP behavior:**
   - Frozen Java `Clock`, seeded `Random`, and disposable DB fixtures are **JUnit/Quarkus test harness concerns**, never global frozen timestamps across independent live HTTP requests. State the boundary explicitly in `scope` and `out` so preparers do not invent cross-request frozen-clock HTTP tests (which force authors into out-of-scope clock hacks).
3. **Specify exact framework SPI signatures and resource ownership:**
   - Vague SPI wording leads authors to wrong overloads (for example `inject(Object)` instead of Quarkus `QuarkusTestResourceLifecycleManager`'s `@Override public void inject(TestInjector testInjector)`). Write the exact Java SPI / package contract in `scope`.
   - Remember Quarkus config ordinals: `QuarkusTestResourceLifecycleManager` system properties (`ordinal 400`) override `@QuarkusTestProfile` config overrides (`ordinal 275`).
   - Ephemeral test teardown must track resources (databases, roles) **created by that instance only** and refuse unmarked DBs or unapproved hostnames **before DDL** via explicit refusal (never falling back to raw `SQLException` or dropping pre-existing roles on setup failure).
4. **Keep specs minimal, single-feature, and strictly scoped:**
   - `TaskPreparer` only exposes committed `public` Java interfaces (`<= 100 KB` per file) from `base_sha`. Do not mention unrelated endpoints or global settings lists in `accept` or `test`; doing so causes preparers to assert unrelated pagination/edge behaviors, forcing authors into out-of-scope edits that reviewers rightfully reject (`reviewer_rejected` / `correction_unchanged`).
5. **Respect author budget, handover, and reviewer limits:**
   - Authors run with `thinkingLevel: 'max'`, a `250k` native context cap, and up to `3` handover sessions. `AEION_HANDOVER_CHECK` carries passed check state across handovers and `factory-checks.ts` instructs the model to finalize (`submit_feedback`) immediately once `run_protected_checks` passes, rather than spending remaining context polishing Markdown.
   - Keep `write_paths` and required deliverables focused (`S`/`M` effort) so one or two focused slices pass unit checks, protected black-box acceptance, and independent two-vote review well inside the session/token budget.

## 4. Checklist before launching a new or updated feature

1. Run catalog generation & check (`generate_features.py --check` + `demo/forum/tools` tests).
2. Confirm every item in `## Acceptance checks` is either:
   - black-box testable via `http://127.0.0.1:8080` (HTTP + Chromium/Playwright) and fails on untouched `origin/main`, **or**
   - covered by a registered transition oracle in `demo/factory/transitions/`.
3. Confirm no assertion conflicts with the `16 KiB` `HTTP 413` guard, cookie `X-CSRF-Token`, or `422` validation envelope.
4. Confirm any new internal Java SPI signature or teardown safety invariant is named explicitly in `**Scope:**` and `## Invariants`.
5. If factory protocol files (`demo/factory/`, `demo/app/`, `demo/flue/`, `demo/openshell/`) changed while implementing an adapter/oracle, run repository checks, merge to `main`, and requalify live admission (`(cd demo && .local/venv/bin/python -m factory.admission --activate)`), then restart the Cockpit daemon.

## 5. Quick diagnosis when a build goes on hold

| Hold / Stop reason | Meaning | Fix path |
| --- | --- | --- |
| `preparation_negative_control_missing` | Prepared `acceptance.mjs` passed all assertions on untouched baseline after retries. | Tighten the feature spec's externally observable baseline delta (`specs_*.py`), or add a registered transition oracle if pure internal SPI/build work. |
| `reviewer_rejected` / `correction_unchanged` | Author satisfied a buggy/out-of-scope contract or reviewers flagged out-of-scope edits. | Do not edit `acceptance.mjs` manually to loosen assertions; inspect `receipt.feedback` / `circuit.votes`, fix the spec or factory prompt, cancel the held build, and re-run cleanly (`reprepare_needed` auto-triggers on retry). |
| `SANDBOX_UNAVAILABLE` | Docker/OpenShell TLS permissions or stale container collision. | Ensure `openshell/setup.py` `normalize_tls_permissions` ran and wait/clear stale gateway sandboxes; `dispatch.py` retries transient stops automatically up to attempt limit. |
| `handover_limit` / `gate.closed` | Author hit session count or `250k` context ceiling. | Split oversized specs (`L` -> smaller `S`/`M` specs); check whether a clean candidate was recovered via `AEION_HANDOVER_CHECK` into review. |
