---
id: 071
sequence: 69
title: "Circuit breaker on repeated failure"
area: agents
size: S
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [059, 068, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 071 — Circuit breaker on repeated failure

## Intent

Stop dispatching an agent after three consecutive failures and alert, so one broken persona does not burn the whole queue's budget.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Persist consecutive failures, cooldown and one half-open probe lease.
2. Apply the breaker before the next otherwise-authorized scheduled slot.
3. Race recovery probes and test success, failure, unknown and admin reset.

**Scope:**

- Persist consecutive failures, open-until timestamp and a single half-open probe lease per agent; defaults are three failures and a fifteen-minute cooldown.
- After cooldown, only the next otherwise authorized scheduled slot may claim one probe; no autonomous paid retry loop is introduced.
- A successful probe closes/reset counts; a failed or unknown probe reopens. An administrator reset is audited and does not enlarge tools, quotas or spend.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Failures are counted, not retried forever; the breaker fails closed.

This invariant and the acceptance cases belong to planned protected check `agora-071`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The third consecutive failed run opens the breaker and prevents further dispatch before cooldown.
- [ ] After cooldown, concurrent ticks admit only one eligible half-open probe; failure/unknown outcome reopens and success closes it.
- [ ] An administrator reset is authorized/audited and cannot bypass quiet hours, budget or cancellation.

**Test scenario:** Freeze the clock and race post-cooldown probes; assert one claim, failure/unknown reopen, success reset and unauthorized/manual-reset refusal.

## Out of scope

- Automatic model or persona changes.
- Retry with a different model.
