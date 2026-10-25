---
type: Runbook
title: "Quality, autonomy and experimental evidence"
description: "Task-level objectives, human-intervention taxonomy, cost and latency formulas, independent verification and valid policy comparisons."
status: draft
sources:
  - id: sources
    resource: ../references/sources.md
    title: "Evaluation guidance and statistical references"
---

# Quality and evaluation

## 1. Freeze what counts as success

For each task family, define the deliverable stage before model assignment: for example,
“a scoped patch passing specified checks and ready for independent Factory review.” Deployment,
merge and production access remain separately authorized actions. The optimizer cannot redefine
the deliverable to make a cheap profile appear successful.

Record task inputs, repository/spec/check versions, permitted boundaries, resource envelope,
deadline, acceptance rubric and outcome-maturity window. The maturity window depends on the
task: immediate check completion, later review, or a declared regression observation period.
There is no universal number of hours that proves correctness.

The authoritative output is the bound artifact and its verified effects, not the agent's final
claim. Use deterministic checks first and calibrated human/model grading for aspects that need
judgment. This follows agent-evaluation guidance; it does not make every passing test sufficient.
[Anthropic evaluation guidance](https://www.anthropic.com/research/demystifying-evals-for-ai-agents),
[OpenAI workflow evaluations](https://developers.openai.com/api/docs/guides/agent-evals)

### Proposed acceptance dimensions

| Dimension | Evidence | Invalid shortcut |
| --- | --- | --- |
| Functional correctness | Independent task checks on exact artifact | Agent says tests pass |
| Scope and compatibility | Diff review, regressions and interface checks | More code or more tool calls means better work |
| Integrity | Protected checker/rubric and clean evaluation environment | Agent edits/deletes the checks to make them pass |
| Boundary compliance | Qualified OPS/CROA evidence where applicable | No reported denial means no policy violation |
| Required usability/maintainability | Task-specific calibrated rubric | One generic “good answer” judge for all tasks |
| Human dependence | Complete intervention channel and repair records | No logged complaint means no human repair |
| Durability | Declared later-review/regression evidence | First green CI run means permanent success |

Quality observations have three states: known pass, known fail and unknown. A pending review,
missing integrity evidence or unobserved human edits cannot become an accepted autonomous task.

## 2. Measure human intervention without discouraging safe behavior

| Intervention kind | Autonomous-work metric | Separately report |
| --- | --- | --- |
| Required governance approval / ordinary final review without repair | Does not count as corrective rescue | Approval count, queue time and reviewer effort |
| Acceptance annotation after the result | Does not change the produced result | Evaluation effort and label provenance |
| Necessary input clarification | Human assistance; no autonomous completion for that attempt | Input ambiguity; do not blame the model by default |
| Direction correction / missing requirement reminder | Corrective assistance | Cause, timing and minutes |
| Manual code/test/artifact repair | Corrective assistance, linked to original task | Repair delta/digest and minutes |
| Environment or tool repair by a human | Human assistance | Infrastructure cause versus agent-caused breakage |
| Cancellation, abandonment or hidden follow-up task | Visible non-success/censored status | Reason, spent cost and unresolved result |
| Channel has no human-activity coverage | Unknown autonomy | Coverage gap; not zero intervention |

The initial user instruction and pre-agreed task inputs are not rescue events. A human repairing
the agent's patch in a new session is still repair of the original task. Preserve task lineage
across restarts and follow-ups. A grader finding a failure is not itself an operational repair.

Correctly asking for missing input or refusing an unauthorized action can be the safest behavior.
Do not reward guessing or suppressing approval prompts. Track this behavior separately; if the
task is expected to refuse, give it a separate pre-defined refusal contract/cohort.

## 3. The triangle as explicit measures

Let `N` be a **pre-registered comparable in-scope offered-task cohort**, selected before routing.
Include router rejections, failures, restarts, deadline misses and abandoned work. Record offered,
admitted and started counts separately. Exclude prohibited/out-of-scope tasks only using the
same pre-assignment rule for every treatment, never because one profile struggled.

The bundled paired-cohort demonstration requires the same task-ID set for every policy;
task order may differ. Missing maturity or intervention-coverage fields yield unknown quality,
not a verified autonomous-success count. This example rule does not require identical task
identities across treatment groups in every real randomized experiment.

For task `i`, define:

```text
A_i = 1 only when the accepted deliverable is independently verified,
      all required integrity/boundary checks hold,
      no corrective/input/environment human help was required,
      intervention coverage is complete,
      and the declared maturity window has completed without disqualifying regression.

A_i = 0 for known non-autonomous or failed outcomes.
A_i = unknown for missing or pending required evidence.
```

Ordinary required governance approval without correction does not change `A_i`; its cost/time
is still shown. The practical claim is autonomous work **inside the approved boundary**, not
removing human authority from the delivery process.

| Metric | Formula / reporting rule |
| --- | --- |
| Verified autonomous acceptance | `sum(A_i=1) / N`, with unknown count and maturity shown |
| Observed finite-cohort quality bounds | `[known autonomous successes / N, (successes + unknowns) / N]` |
| Assisted acceptance | Accepted tasks requiring human help / same `N` |
| Corrective effort | Total measured corrective minutes / `N`; coverage shown |
| Verified autonomous goodput | Autonomous successes inside deadline / cohort wall-clock exposure |
| Cost per autonomous success | `sum(all attributable task costs) / sum(A_i=1)` |
| Deadline success | Tasks meeting the frozen acceptance-stage deadline / `N` |
| Delayed regression | Disqualified earlier acceptances / declared mature acceptance cohort |
| Outcome coverage | Tasks with required outcome/intervention evidence / `N` |
| Usage coverage | Requests with resolved charge/quantity evidence / independently observed requests |

The finite-cohort quality bounds are missing-data bounds, not statistical confidence intervals.
An unknown must not enter a learner as a fabricated binary failure or success. For a production
quality gate, use conservative bounds or a declared missing-data model; do not assume missingness
is random. Publish both complete mature cohorts and pending cohorts.

### Cost scope

```text
C_task = inference attempts + paid native/external tools + sandbox compute
       + task-attributable evaluation + allocated observability
       + separately stated human labor allocation, if chosen
```

Include failures and escalation/restart costs in the numerator. State gross consumption versus
incremental cash spend; a fixed subscription is an explicit allocation. Do not mix currencies,
estimated amounts, credits, invoices and allocations into an unexplained scalar.

If no task succeeds, cost per autonomous success is undefined. If cost or outcomes are incomplete,
the ratio is provisional. Report known charges, estimated charges and unresolved exposure beside it.

### Time scope

Report p50/p95 task wall time and time to verified acceptance, plus queue/setup/tool/inference/
governance decomposition. Report failed/timeout tasks and completion coverage alongside successful
task latency. A fast-failing profile must not win by disappearing from the latency distribution.

Do not sum parallel work into elapsed time or claim provider TTFT is the whole task duration.
When observation ends before task completion, retain right-censoring; v0 should wait for a fixed
mature cohort rather than invent a duration. Later survival analysis needs an explicit method.

## 4. Optimize constraints before preferences

The proposed policy objective is:

```text
minimize expected all-in cost for a comparable task class
subject to:
  authorized and qualified profile
  conservative quality estimate >= task-class quality floor
  declared deadline/tail-latency requirement
  admitted budget exposure <= allowed budget
  privacy, context, tool-state and governance requirements
```

Maintain a Pareto view of quality, cost and elapsed time. If several profiles remain, apply an
explicit owner-selected preference: lower cost, lower tail latency, or greater verified quality.
If no profile satisfies the requirements, report infeasibility and stop/checkpoint appropriately.
Do not silently lower the quality floor to keep the agent busy.

An exploratory scalar reward may help a later learner, but retain the full outcome vector and
hard constraints. A weighted average alone can trade a policy violation or human repair against
a small cost saving. Safety constraints never become reward penalties that the optimizer may buy.

## 5. Build an informative task corpus

Start with representative Factory work: a bounded bug fix, small feature, scoped refactor,
test/diagnostic fix and documentation change. Split by language/toolchain, repository size,
context band and risk; do not fragment further than the evidence supports.

Include known troublesome cases: ambiguous requirements, flaky dependencies, long context,
multi-step tool use, partial failures, incompatible model tooling and a justified refusal.
Keep an untouched holdout and known-good controls. Separate capability tasks from regression
tasks; the former seek improvement, the latter protect already accepted behavior.

Protect hidden acceptance material outside workload access. Re-run checks in a clean environment
on the exact exported artifact with named toolchain and resource envelope. Tests authored only
by the same agent are useful development evidence, not automatically independent acceptance.

Report CPU/RAM/timeout/concurrency differences. Resource settings themselves can alter coding
eval scores; they are part of the treatment unless intentionally held constant.
[Infrastructure-noise evidence](https://www.anthropic.com/research/infrastructure-noise)

## 6. Judge policy

Use an LLM judge only where a rubric needs it. Give it delimited untrusted artifacts, no execution
tools, no policy-write access and permission to return `unknown`. Version judge model, prompt,
rubric and evidence selection. Never export hidden reasoning to score a task.

Calibrate on human-labelled pass/fail/edge cases. Track false acceptance and false rejection,
not just average agreement. Test prompt injection inside diffs/tool outputs and adversarial
answers that claim to have passed. Use a different model family where it helps reduce correlated
errors, but do not treat “different model” or a fresh AI reviewer as independent certification.

Keep evaluation cost and label delay in the ledger. An evaluator more expensive than the saved
inference can erase an apparent win. Sampling judges is allowed for analysis with inclusion
probabilities; it must not erase the required acceptance evidence for counted autonomous success.

## 7. Compare policies, not unmatched dashboard averages

1. Freeze cohort, hypothesis, control profile/policy, minimum worthwhile gain, non-inferiority
   margin, primary metric, stop rules and delayed-regression window.
2. Assign whole tasks to control/candidate with a logged randomized procedure where safe.
   A task-level bundle includes its retry/escalation policy, not just its first model.
3. Run paired tasks in isolated environments for offline comparisons. Repeated trials of the
   same task/repository are clustered, not independent new task samples.
4. Stratify or block by task family and infrastructure/time window; estimate the aggregate
   using declared workload weights. Watch for a gain caused only by easier candidate tasks.
5. Show counts, missing data, intervals and absolute differences. No universal “30 sessions”
   or “100 calls” guarantees a reliable decision; power depends on baseline and desired effect.
6. Promote only after quality, time, cost, coverage, policy and rollback gates all hold.

As a scale illustration, estimating a Bernoulli rate near 0.9 with a roughly 0.03 two-sided
half-width at 95% requires about `1.96² × 0.9 × 0.1 / 0.03² ≈ 385` independent observations
under a normal approximation. This is **not** a sample-size calculation for a two-arm
non-inferiority test, nor permission to ignore clustering, sequential looks or missing labels.

Use a suitable binomial interval for a fixed-sample single-rate summary; use paired/clustered
methods for the actual policy comparison. Cost and p95 latency need uncertainty appropriate
to skew, censoring and task clustering. Repeated online decisions need a pre-specified
sequential design or valid confidence sequences, not daily reuse of an ordinary 95% interval.
[Sequential inference reference](https://arxiv.org/abs/1810.08240v9)

### Off-policy evaluation, later

For task context `x`, selected profile `a`, outcome `y`, logged assignment probability `p(a|x)`
and proposed policy `pi`, importance weighting uses `pi(a|x)/p(a|x)`. A doubly robust estimate
combines those weights with an outcome prediction. Log the actual propensity at decision time,
the eligible set and policy version. A deterministic rule has zero support for alternatives.
[Doubly robust evaluation](https://arxiv.org/abs/1103.4601v2)

Check overlap and weight variance/effective sample size; disclose clipping bias and held-out
model fitting. With many adaptive within-task switches, a one-step estimator on terminal quality
is not valid: use whole-policy task randomization or a suitable sequential causal method.
Do not apply every task's success label equally to all of its LLM calls as if each caused it.

An offline replay can reproduce eligibility and policy decisions on recorded features. It
cannot reveal what a different model would have done to later tools, source files or user behavior.
Counterfactual execution requires isolated reruns, with no side effects replayed into production.

## 8. Promotion evidence

Every candidate needs a compact report: cohort/split hashes, task and profile versions, counts,
quality/assistance/regression results, latency tails, cost basis and completeness, uncertainty,
failed cases, authorization/compatibility evidence and rollback target. Mark `insufficient_evidence`
when an essential check cannot be established. More autonomy is not the default tiebreaker.

See the [worked example](../../examples/README.md) for arithmetic illustrating why per-call price
and task economics can disagree. Its numbers are deliberately synthetic and establish no ranking.
