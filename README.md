# Æion Observability

**Measure agent work and design better cost / speed / quality decisions — independently usable.**

Use the contracts and examples with an existing agent workflow. No other Æion checkout or
running SpaceShip service is needed. The bundled example runs locally without a provider key.

Part of the modular [Æion SpaceShip framework](https://github.com/OualidGuennif/aeion-spaceship).
[Factory](https://github.com/OualidGuennif/aeion-factory) ·
[OPS](https://github.com/OualidGuennif/aeion-ops) ·
[CROA](https://github.com/OualidGuennif/aeion-croa) ·
[Observability](https://github.com/OualidGuennif/aeion-observability) ·
[SpaceShip](https://github.com/OualidGuennif/aeion-spaceship).
See the [module comparison and examples](https://github.com/OualidGuennif/aeion-spaceship/blob/main/docs/modules.md).

**Research and framework proposal — checked 2026-10-23.**

Observe complete coding-agent tasks, connect their execution to verified outcomes, and use
that evidence to choose models, providers and inference settings. Optimize **cost, elapsed
time, and correct completion without corrective human intervention** within fixed authority.

This folder contains a sourced design, offline examples and an opt-in [Docker demo](demo/README.md)
with Langfuse, OpenTelemetry, Hindsight, claude-mem and OpenCode build agents isolated in NVIDIA OpenShell. The offline examples need no service or
key. The demo operates on four frozen synthetic task contracts; no cost or quality improvement has been
measured on representative Æion workloads.

## Run the Docker demo

See the [demo runbook](demo/README.md) for private local setup, ports and verification. It
includes a deterministic checkpoint at **250,000 reported input-context tokens**, followed by
a fresh agent session carrying a durable HANDOVER.md, files and check results. An independent
relay counts requests before forwarding and reserves output/framing inside a 300k admission
budget. Provider-count qualification assumptions and billing limits are explicit in the runbook.

The [2026-10-27 qualification record](work/validation.md#openshell-migration-and-expanded-model-lab--2026-10-27)
includes a corrected 40-attempt, five-model OpenShell matrix: 36 accepted outcomes, four
retained CLI failures and $0.368068181 in native estimates. It also records four-tool
readbacks, a measured Auto build and the synthetic 250k handover. These small synthetic
contracts with real CLI calls do not establish general model superiority or invoice costs.

## Try the offline example

Python 3.9+ and the standard library are sufficient:

```sh
git clone https://github.com/OualidGuennif/aeion-observability.git
cd aeion-observability
python3 examples/compare_cohorts.py
```

Expected: the fictional `cheap` cohort costs $72 for six autonomous successes ($12 each);
`balanced` costs $82 for nine (about $9.11 each). This illustrates why all attempts and
corrective work matter. **These are synthetic examples, not measured model improvements.**
See [worked examples](examples/README.md). Run regression checks with
`python3 -m unittest discover -s tests -v`.

## Recommended foundation

1. Keep **Æion Factory** as the development method, **Agentic OPS** as the execution boundary,
   and **CROA** as the separate governance/audit reference.
2. Use **OpenTelemetry/OTLP** as transport, with a pinned GenAI convention mapping and small
   `aeion.*` extensions. Keep accounting and task outcomes complete even when traces are sampled.
3. Evaluate **Langfuse core** for traces, datasets and evaluations. Reuse an existing APM for
   infrastructure metrics/logs. The contracts remain independent of either backend.
4. Start with **observe → shadow recommendations → a bounded canary**, using a small catalog
   of approved profiles. Keep one model per task initially; allow a separately tested checkpoint
   escalation later. A dashboard is not the controller.
5. Select an execution profile only after capability, privacy, budget, deadline and quality
   eligibility checks. Unknown evidence never becomes a successful task or a zero-dollar call.

These are Æion recommendations, not upstream guarantees. The [state of the art](knowledge/references/state-of-the-art.md)
compares alternatives and explains the choice; the [source register](knowledge/references/sources.md)
links the primary documentation and papers behind it.

## Read the dossier

| Document | What it settles |
| --- | --- |
| [Framework specification](knowledge/components/observability.md) | Responsibilities, architecture, interfaces and invariants |
| [State of the art](knowledge/references/state-of-the-art.md) | Standards, tools, routing research and evidence limits |
| [Provider capabilities](knowledge/references/provider-capabilities.md) | Exact OpenRouter/DeepInfra controls and harness limitations |
| [Telemetry contract](knowledge/operations/telemetry-contract.md) | Task/session/attempt identity, events, usage and normalization |
| [Quality and evaluation](knowledge/operations/quality-and-evaluation.md) | Autonomous success, human intervention, experiments and statistics |
| [Control loop](knowledge/operations/control-loop.md) | Decision algorithm, real-time reactions, escalation and rollback |
| [Security and reliability](knowledge/operations/security-and-reliability.md) | Trust, content handling, outages, budgets and failure recovery |
| [Implementation and qualification](knowledge/operations/implementation-plan.md) | Delivery phases, dashboards, acceptance scenarios and open questions |
| [Worked examples](examples/README.md) | Synthetic events, request fragments, policy and cost/quality arithmetic |
| [Sources and credits](knowledge/references/sources.md) | Evidence register, research depth and attribution |
| [Current work](work/current.md) | Current scope and next implementation decision |
| [Docker demo specification](knowledge/components/docker-demo.md) | Langfuse/OTel/OpenCode pilot, context gate and evidence limits |

## What “real time” means here

| Time of decision | Available evidence | Permitted optimization |
| --- | --- | --- |
| Before a task | Task contract, approved profiles, past verified outcomes | Choose an eligible profile |
| Before the next request | Health, deadline, reservations, context/tool state | Apply an already approved fallback or setting change |
| During a request | First-token delay, stream progress, cancellation state | Bound waits or cancel; no assumed token-level model migration |
| At a safe checkpoint | Artifact/check results and portable state | A qualified escalation or clean restart |
| After verification | Accepted artifact, repairs, actual usage, delayed regressions | Update a future policy candidate and evaluate it |

Provider performance preferences alone do not predict whether the whole task will succeed.
Early tool results and errors are useful signals; they are not terminal quality labels.

## Both authentication paths remain

- **Claude subscription/token via its supported CLI flow:** native session telemetry and
  outcome evaluation; treat monetary per-call costs as estimates/allocation, not invoices.
  Do not infer arbitrary provider or inference-parameter control from this path.
- **OpenRouter or DeepInfra API:** request-level configuration is possible where the actual
  harness exposes it. Qualify each protocol/model/provider tuple; an OpenAI-compatible API
  and an Anthropic-compatible CLI path are separate integrations.

The framework does not require abandoning the subscription path. API access is the more
controllable experimental path for arbitrary model/provider/parameter combinations.

## The objective that matters

Use verified autonomous acceptance rate as a quality constraint, then compare cost and
time on that same task cohort. A useful economic measure is:

```text
cost per verified autonomous success =
  all attributable cohort costs / number of verified autonomous successes
```

Include failed attempts, retries, evaluation and sandbox costs. Report the accounting basis
and unresolved amounts. Zero successes makes this measure undefined, never zero.
Also report human repair minutes, deadline failures, telemetry coverage and delayed regressions.

## Scope and reuse

This research follows Factory's specification/evidence structure without copying its entire
tooling into a research folder. It proposes interfaces callable by Factory and consuming OPS
events; it does not modify those projects. [Original Æion material is MIT licensed](LICENSE).
Upstream software, documentation and papers retain their own licenses; see [credits](CREDITS.md).

This repository publishes the framework, research, offline examples and a local Docker pilot.
Production runtime qualification and a routing controller remain subsequent work.

Document/link checks, source fingerprints, example calculations and consistency checks are
recorded in the [research validation record](work/validation.md). Runtime qualification remains
the separate planned work described above.
