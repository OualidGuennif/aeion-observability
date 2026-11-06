# Æion Observability

**See what your coding agents really deliver. Pay for results, not attempts.**

A framework for observing complete coding-agent tasks, linking them to verified outcomes, and
choosing models, providers and settings from that evidence, with offline examples and an opt-in
local factory that builds real features end to end.

[Framework](#the-framework) · [Try the examples](#try-the-examples) · [Factory pilot](#the-factory-pilot) · [Repository map](#repository-map) · [Development](#development)

## What is here

| Part | What you get | Where | You need |
| --- | --- | --- | --- |
| **Framework** | The design: telemetry contract, quality measure, control loop, security | [`knowledge/`](knowledge/index.md) | Nothing; read it |
| **Examples** | Synthetic events and cost/quality arithmetic that check the contracts | [`examples/`](examples/README.md) | Python 3.9+ |
| **Factory pilot** | A local Docker demo that turns a Markdown spec into a reviewed pull request on a real product | [`demo/`](demo/README.md) | Docker, Node, provider keys |

Each part works without the others.

**Status.** The framework and examples are complete as a design. The pilot runs end to end on
[`aeion-autonomous-forum`](https://github.com/OualidGuennif/aeion-autonomous-forum), but no
product feature has completed the whole circuit to main yet, and no cost or quality improvement
has been measured on real workloads. Synthetic examples are never benchmark evidence.
[Current work →](work/current.md) · [Dated evidence →](work/validation.md)

## The framework

One number decides whether a setup is better:

```text
cost per verified autonomous success =
  all attributable costs / number of verified autonomous successes
```

Failed attempts, retries, evaluations and sandboxes all count. Zero successes makes it undefined,
never zero. Human repair time, missed deadlines and telemetry coverage are reported next to it.

In short:

- **OpenTelemetry/OTLP** carries the data; accounting and outcomes stay complete when traces are sampled.
- **Langfuse** is evaluated for traces and evaluations; the contracts do not depend on it.
- Rollout goes **observe → shadow recommendations → bounded canary**, with a small catalog of
  tested profiles instead of tuning every parameter.
- Both access paths stay: a **Claude subscription** through its CLI, and **OpenRouter or DeepInfra APIs**.
- Observability recommends; it never widens an agent's permissions or removes a review gate.

| Read | To learn |
| --- | --- |
| [Framework specification](knowledge/components/observability.md) | Responsibilities, architecture, interfaces, invariants |
| [Telemetry contract](knowledge/operations/telemetry-contract.md) | Task, session and attempt identity; events; usage |
| [Quality and evaluation](knowledge/operations/quality-and-evaluation.md) | Autonomous success, human intervention, experiments |
| [Control loop](knowledge/operations/control-loop.md) | When a decision may change during a task |
| [Security and reliability](knowledge/operations/security-and-reliability.md) | Trust, content handling, outages, budgets |
| [Provider capabilities](knowledge/references/provider-capabilities.md) | Exact controls per provider and harness |
| [State of the art](knowledge/references/state-of-the-art.md) · [sources](knowledge/references/sources.md) | Alternatives and the primary sources behind each choice |

## Try the examples

No key, no service:

```bash
git clone https://github.com/OualidGuennif/aeion-observability.git
cd aeion-observability
python3 examples/compare_cohorts.py
python3 -m unittest discover -s tests -v
```

The fictional `cheap` cohort costs $72 for six successes ($12 each); `balanced` costs $82 for
nine (about $9.11 each). The cheaper cohort costs more per success.
[Worked examples →](examples/README.md)

## The factory pilot

You pick a feature in a local cockpit; the factory builds it, checks it and publishes it only
when everything agrees:

```text
Markdown spec ─► preparation ─► author agent (Flue + Pi, tools only inside an OpenShell sandbox)
   ─► protected checks ─► two independent reviewer models
   ─► rejected or failed gate? up to two automatic correction rounds, then you decide
   ─► pull request ─► CI on the exact head ─► red CI? the same correction rounds
   ─► product main
```

Every step is traced, budgeted (15 USD a day per repository) and kept as a receipt. The author
has no network, reviewers never share the author's model family, and an uncertain step stops the
build instead of guessing.

[Setup and runbook →](demo/README.md) · [Execution contract](knowledge/components/factory-flue.md) ·
[Cockpit](knowledge/components/operator-cockpit.md) · [Trust model](demo/factory/trust-model.md)

## Repository map

| Folder | Contents |
| --- | --- |
| `knowledge/` | The framework docs. Start at [the index](knowledge/index.md). |
| `examples/`, `tests/` | Offline synthetic fixtures and their tests |
| `demo/` | The factory pilot: `app/` cockpit and relay, `factory/` supervisor, `flue/` agents, `openshell/` sandbox, `forum/` product catalog, `tests/` |
| `work/` | Current work and the validation record |
| `tools/`, `efficiency/`, `loops/`, `.claude/`, `.agents/`, `.grok/`, … | Development tooling from the template |

## Development

Built from the [Æion Factory](https://github.com/OualidGuennif/aeion-factory) template (v2.1.1).
Agent instructions: [AGENTS.md](AGENTS.md).

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s demo/tests -v
tools/knowledge/knowledge-check && tools/knowledge/doc-links && tools/repo-health/repo-health
```

## License

[MIT](LICENSE) for original material; upstream work keeps its own license ([credits](CREDITS.md)).
Security reports: [SECURITY.md](SECURITY.md).
