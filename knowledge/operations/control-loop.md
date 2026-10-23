---
type: Runbook
title: "Bounded online session optimization"
description: "Proposed control modes, profile selection, fast operational reactions, safe escalation, delayed quality learning and rollback."
status: draft
sources:
  - id: quality
    resource: quality-and-evaluation.md
    title: "Objective and promotion evidence"
  - id: providers
    resource: ../references/provider-capabilities.md
    title: "Actual provider and harness actuation surfaces"
---

# Control loop

This is a proposed algorithm and operating contract, not an implemented controller. The example
policy is deliberately **shadow only**. Neither a model analyst nor a telemetry backend receives
authority to expand runtime permissions or change provider credentials.

## 1. Separate operating speeds

| Loop | Inputs | Decisions | Execution boundary |
| --- | --- | --- | --- |
| Fast operational loop | Current request health, deadline, reservation and stream progress | Admit, wait within deadline, bounded retry, approved fallback, cancel | Trusted adapter/supervisor, before dispatch or cancellation |
| Task/checkpoint loop | Verified milestones, portable state, repeated failures and remaining budget | Continue, use an approved escalation, checkpoint, restart or ask for missing input | Between requests/tool cycles, with no unresolved effects |
| Quality-improvement loop | Mature task outcomes, intervention evidence, complete cost and experiments | Propose/publish a new policy version after its gates | Applies to future assignments; no silent mutation of live treatment |

“Fast” does not mean the dashboard can interrupt an API request. An ended span, Stop hook or
post-response Broadcast arrives too late for that request's first-token timeout. Those actions
need a direct request timer/cancellation channel at the adapter. Stock CLI observation alone
supports analysis/recommendations, not universal per-request actuation.

Keep only the mechanisms needed for the selected harness. Do not run a second LLM on every
step to decide which LLM to use when a deterministic task/profile rule gives the same information.

## 2. Operating modes

| Mode | Behavior | Gate to next mode |
| --- | --- | --- |
| `observe` | Capture and evaluate; existing model choice stays external | Correct joins, privacy, usage and outcome coverage |
| `shadow` | Compute/log recommendations without applying them | Decision replay, compatibility and offline evaluation |
| `canary` | Apply an approved policy to a bounded low-impact task cohort | Pre-registered quality/cost/time and rollback gates |
| `bounded_adaptive` | Choose among previously qualified profiles within explicit limits | Continuous monitoring, refreshed evidence and scoped authorization |

No mode authorizes broad deployment, automatic merge, tool-capability expansion, a new data
region or bypass of human review. Mode transitions are versioned control-plane changes under
Factory's review process. New models start in evaluation/shadow, not as untested outage fallbacks.

## 3. Profile catalog and decision context

Begin with perhaps three roles: a baseline, a lower-cost candidate and a stronger recovery
candidate. This is an illustrative catalog size, not a requirement for three models. One model
at two effort levels may be enough; keep only bundles with a concrete experimental purpose.

Each profile specifies exact model/revision where available, protocol/auth mode, allowed serving
providers, supported parameter bundle, context/tool capability, privacy class, retry/cancel
behavior, resource envelope, price snapshot and qualification/evaluation references.

The controller reads only bounded pre-decision features:

| Feature group | Examples | Evidence restriction |
| --- | --- | --- |
| Task | Frozen family/risk/data class, deadline, acceptance stage | Supplied before assignment by trusted intake |
| Context | Estimated tokens/window, unresolved tool state, cache affinity | Preserve estimate and tokenizer/model mapping |
| Progress | Approved milestone/check results, current artifact digest | Agent self-confidence is not verified progress |
| Failures | Error class, repeated tool/check failure, truncation | Distinguish infrastructure, capability and reasoning causes |
| Budget | Known spend, reserved exposure, unresolved charges, remaining limits | Trusted atomic ledger, not dashboard sums |
| Health | Recent per-endpoint error/latency, sample count, age, circuit state | Defined window and freshness; stale data cannot grant eligibility |
| Evidence | Mature quality/cost/time estimates for comparable profiles/tasks | No future outcome or holdout answer in decision features |

Use non-content task metadata first. Learned semantic difficulty classifiers see code/prompt
content and add cost/latency/privacy surface; introduce one only if it beats that baseline.

## 4. Deterministic decision algorithm

The following pseudocode deliberately names logical interfaces, not real SDK methods:

```text
decide(boundary, task, state, approved_policy, catalog, health, ledger):
    validate policy integrity, scope, expiry and task binding
    validate state/cancellation/checkpoint status
    if required authority or accounting boundary is unavailable:
        refuse automated dispatch; preserve checkpoint and reason

    candidates = approved_policy.profiles_for(task.family, boundary)
    remove profiles failing auth, data-region, privacy or OPS allowlist
    remove profiles failing model/protocol/context/tool/parameter qualification
    remove profiles requiring an unsafe state migration or unresolved tool cycle
    remove profiles with open circuit or expired mandatory metadata
    remove profiles without a defensible bounded request exposure
    remove profiles whose exposure/deadline cannot be admitted

    if outcome evidence is adequate:
        retain profiles meeting the declared conservative quality/time gates
        select by the declared cost/speed preference, including switch overhead
    else:
        use only the explicitly approved baseline for this evidence-poor condition
        mark quality evidence insufficient; do not claim the floor was proven

    if no eligible approved profile remains:
        checkpoint/defer/refuse according to the task contract
    else:
        record full decision, exclusions, propensity and immutable policy version
        atomically reserve the selected request's exposure
        recheck cancellation and policy validity at dispatch
        dispatch through the qualified adapter and record application acknowledgement
```

Reservation failure returns to a bounded admission path; it does not send an unaccounted request.
Handle decision-record failure according to the required evidence policy. For a protected
transition, a sampled trace or asynchronously buffered log is not the required durable audit.

Illustrative profile scoring after hard eligibility:

```text
minimize predicted remaining all-in task cost + measured switch/restart overhead
subject to lower quality bound >= class floor
           conservative completion-time estimate <= remaining deadline
```

Predictions are uncertain estimates, not hard guarantees. Keep them labelled and test calibration.
Do not sum p95 request latencies to claim an accurate p95 task bound. If the approved baseline
also lacks sufficient evidence, the operator may run an explicit measurement pilot; the report
must retain that limitation rather than manufacture confidence.

## 5. Real-time decision table

| Signal | Immediate response | Next improvement experiment |
| --- | --- | --- |
| Rising 429/5xx or transport errors | Bounded backoff/jitter within deadline; open circuit; approved healthy endpoint only | Same-model provider/route comparison |
| Authentication/permission error | Stop affected path; no credential-mode bypass | Repair operator configuration |
| Unsupported parameter/context/tool error | Reject profile; do not silently strip a required control | Qualify corrected bundle/protocol |
| Long first useful action, healthy provider | Wait/cancel using profile deadline; optionally use a qualified faster route next request | Compare model/effort/tier with task completion held constant |
| Repeated same test failure with no verified progress | A bounded recovery/checkpoint decision; classify root cause | Stronger profile or better context/tooling, separately tested |
| OOM, disk/PID limit or slow dependency install | Record infrastructure failure; respect fixed envelope | Resource/setup investigation, not automatic model escalation |
| Output truncated / incomplete tool arguments | Do not execute partial tool call; bounded repair/continuation only | Output-cap sweep including failure/retry cost |
| Repeated compaction/context loss | Preserve artifact/state and assess restart portability | Context strategy and cache study |
| Spend/exposure nearing limit | Refuse new unadmittable calls; allow only budgeted cleanup/checkpoint | Reallocate future task budgets after evaluation |
| Native telemetry goes stale | Stop learning; use allowed fixed baseline or refuse where required evidence is mandatory | Repair instrumentation/capture |
| Human corrective work or delayed regression increases | Halt candidate promotion; roll back future assignments | Inspect failure cohort and verifier calibration |
| Model/provider/catalog revision changes | Treat as a new or requalification-required profile | Repeat compatibility/regression checks |

All thresholds belong to a versioned policy with rationale and observed calibration. Example
counts such as “three repeated errors” are a starting hypothesis, not proof that a task is stuck.
Repeated commands may be legitimate; the decisive signal is a task-specific lack of progress.

## 6. Switching and escalation

### v0: choose once per task

Choose an approved profile at task admission and keep it sticky. Learn from the terminal result.
Permit only qualified same-model outage handling under the frozen fallback policy. This keeps
task-level attribution clear and preserves cache/context assumptions.

ORACLE provides a relevant research example of task/model/verifier binding and delayed feedback.
It does not prove that its local scheduling machinery transfers to hosted APIs.
[ORACLE v4](https://arxiv.org/html/2607.22465v4)

### v1: one bounded checkpoint escalation

Add this only if experiments show benefit over the fixed baseline. At a checkpoint:

1. Quiesce/drain the current interaction. Resolve or cancel pending tools with recorded effect
   status; do not replay a tool merely because a model request timed out.
2. Export an immutable artifact plus a bounded handoff: task contract, verified facts, checks,
   unresolved issues and allowed capabilities. Treat model-authored summaries as untrusted.
3. Verify the target context window, tool schema, protocol, privacy and auth eligibility.
4. Carry provider-signed/opaque continuation state only where documented compatible. Never
   translate signed thinking, provider response IDs or hidden state by guesswork.
5. Include re-prefill/cache miss, repeated setup, discarded attempts, summary verification and
   possible restart in the proposed cost/time. A smaller token price can lose after switching.
6. Apply a bounded escalation count and minimum predicted benefit. Record `switch_reason`,
   source/target profile, evidence and actual acknowledgement.
7. If in-place migration is unqualified, start a clean run with the same task ID and explicit
   artifact lineage. Prevent duplicate external side effects.

SWE-Router illustrates why early trajectory evidence may help a continue/escalate choice.
Its described stronger-model branch starts again from the original prompt; savings cannot be
calculated as if the exploratory work were free.
[SWE-Router](https://arxiv.org/abs/2607.00053)

Do not oscillate after every slow call. Use a policy-defined hysteresis margin, minimum dwell
boundary and a task-level switch budget. Preserve the treatment ID for the whole strategy;
report its mixed-model outcome rather than crediting the last model with all success.

## 7. Parameter tuning order

1. Fix observable execution waste: broken tools, repeated setup, irrelevant context, flaky checks
   and unclear acceptance. These may dominate model latency/cost.
2. Compare a small set of model/provider profiles on complete tasks.
3. Sweep supported effort/reasoning settings for each surviving model. Effort values do not
   represent the same computation across models.
4. Tune output caps and timeouts against actual truncation, retries and acceptance. Lower caps
   can increase total work or cut required tool arguments.
5. Evaluate cache/prefix locality and service-tier policy with measured reuse and pricing.
6. Tune sampling parameters only where accepted by the model and a measured task benefit exists.
   Do not optimize temperature and `top_p` simultaneously without a controlled hypothesis.

Tune one factor or a deliberately small factorial bundle at a time. Freeze prompts, tools,
resources and checks where possible; otherwise label the combined intervention honestly.

DeepInfra documents reasoning and service-tier controls; OpenRouter documents a normalized
reasoning object and provider selection. Map semantic intent through per-profile adapters,
not a universal dictionary of interchangeable values.
[DeepInfra reasoning](https://docs.deepinfra.com/chat/reasoning),
[OpenRouter reasoning](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)

## 8. Delayed learning and policy publication

The quality loop is asynchronous. Dispatch can continue under its approved snapshot while
outcomes arrive. Maintain pending-label counts and assignment times; never temporarily label
every unfinished task a failure or success. Large outstanding candidate exposure may require
pausing further exploration until results mature.

After enough representative labels, consider a task-level constrained contextual bandit. Use
explicit allowed arms, logged propensities, a fixed control cohort and a capped exploration
budget. Count failed experiments, judge cost and data collection in that budget. WISERouter
motivates workload-budget learning, with assumptions that do not automatically hold for
dependent agent steps. [WISERouter limitations](https://arxiv.org/html/2607.23765v1)

Policy publication must bind model/parameter/catalog/evaluator versions, cohort evidence,
scope, expiry and rollback target. Distribute immutable snapshots atomically. A running task
keeps its snapshot unless an explicit incident rule safely cancels or changes it. A workload
cannot edit the protected policy file and make its next model request more privileged.

## 9. Rollback and controller observability

Log decision latency, health feature age, candidates/exclusions, selection and propensity,
reservation/application success, model switches, unknown results and policy versions. An LLM
explanation is optional; deterministic reason codes are required.

On quality regression, privacy/control violation or accounting uncertainty beyond the allowed
policy, stop the canary and restore the last compatible approved profile for future work.
In-flight cancellation and state recovery follow the adapter's qualified semantics. Rollback
does not assume an already retired endpoint or incompatible model state still works.

Use a kill switch outside the agent. If the optimizer is down, use an explicitly authorized
fixed baseline only when mandatory evidence, budget and enforcement remain available; otherwise
checkpoint/refuse. A monitoring outage must never widen access.
