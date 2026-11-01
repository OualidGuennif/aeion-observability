---
name: debug
description: Investigates a reproducible bug, failed check or unexpected runtime behavior before changing code; traces evidence to the failing boundary and verifies the regression.
---

# Debug a failure

1. Capture the failing input, exact command/error and expected behavior. Reproduce it; if it
   cannot be reproduced, gather bounded evidence instead of inventing a cause.
2. Read the relevant spec, callers, configuration and recent diff. Follow the actual execution
   path to the first failing boundary. Distinguish observations, confirmed causes and hypotheses.
3. Form one falsifiable hypothesis. Use the smallest diagnostic or experiment that can reject
   it. Never print secrets or complete request/environment dumps as instrumentation.
4. Add a regression test when behavior changes: demonstrate the failure, apply the smallest
   root-cause fix, and verify success plus relevant negative paths. Keep assertions meaningful.
5. Run the owning checks, update the affected Knowledge/spec and report remaining uncertainty.
   Stop accumulating fixes when the hypothesis fails; return to evidence.

Adapted from the investigation sequence in obra/Superpowers `systematic-debugging` (MIT).
Attribution: `CREDITS.md`. Æion Factory's existing authority, test and sign-off rules still apply.

## Diagnosis and stopping conditions
For an intermittent failure, vary one factor at a time: input/state, dependency version,
execution order or concurrency. Compare the same command in isolation and in the failing
sequence before blaming the environment. Preserve a small sanitized repro artifact.

If a hypothesis fails, record what falsified it and remove diagnostic changes before trying
another. Do not stack speculative fixes. For stateful bugs, exercise duplicate/retry and
partial-failure recovery, not only the eventual success. If evidence remains insufficient,
report the smallest missing observation and an instrumentation/reproduction proposal.

Completion evidence: observed failure, confirmed cause (or remaining hypothesis), smallest
fix, regression command/result and scope not tested. Addy Osmani's debugging-and-error-recovery
and ECC's diagnostic profiles supply techniques; they do not launch specialist agents.
