---
name: spec
description: Writes or updates the spec sections of a component or feature before its code changes - intent, data sources, inputs, outputs and refusals, invariants with their tests, determinism, acceptance checks, out of scope. Use when a feature is added or a component's behaviour changes.
---

# Spec

## Overview
The spec is the source of truth; the code implements it. Format: `knowledge/policies/specs-first.md`.

## When to use
A new feature, a changed contract, a new refusal or error. Not for a refactor that keeps behaviour.

## Process
1. Find the component doc (`knowledge/components/`), or start one from `_template.md`.
2. Write Intent and Outputs first (every refusal and error code), then Inputs, Invariants (each naming its test), Determinism, Acceptance checks (commands), Out of scope.
3. Add the code files to `sources`, and a `Spec: knowledge/components/<doc>.md` line to each file.
4. Write the acceptance checks as tests that fail today.
5. `tools/knowledge/knowledge-check` and `tools/knowledge/doc-links`.

## Rationalizations
| Excuse | Rebuttal |
| --- | --- |
| "The code is the spec" | The code says what it does, not what it must do or refuse. |

## Red flags
An invariant with no test; an output section without its errors.

## Verification
- [ ] The eight sections exist; each invariant names a test.
- [ ] The new acceptance tests fail before the change.

## Specify observable failure behavior
For a changed boundary, state who may call it, accepted data, stable outputs/errors and
side effects. Identify compatibility for existing callers and stored records. For retries
or concurrent writers, name identity/deduplication, transaction/ordering assumptions and
recovery after partial failure; do not claim exactly-once delivery without a guarantee.

Map each acceptance case to an observable result and an actual owning test/command. Where
behavior is already specified, amend that contract instead of creating a parallel document.
For documentation-only work use relevant structure/link checks, not contrived failing code tests.
