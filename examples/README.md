# Synthetic examples

Try the bundled calculation with Python 3.9+ and no provider account:

```sh
python3 examples/compare_cohorts.py
python3 examples/validate_fixtures.py
```

This prints fictional cohort results. The tool includes failed/assisted costs, preserves unknown
quality, and returns an undefined ratio when no autonomous task succeeds. It never controls a
session or proves a model is better. See the regression checks under `tests/`.

The fixture validator rejects duplicate JSON object keys, non-finite numbers and inconsistent
policy, task/run, artifact/check or charge references. It preserves the example's disabled
observe/shadow controls and deduplicates identical deliveries by producer/boot/event identity;
conflicting duplicates fail. It only validates these bundled fictional scenarios, not arbitrary
production events, provider compatibility, privacy enforcement or actual task success.

Every record here is fictional, marked `example_only=true`, and uses proposed Æion contracts.
There are no live credentials, captured prompts, production task IDs or executed provider results.
Repeated hexadecimal digests illustrate identity binding; they do not hash real source/artifacts.
No formal production JSON Schema or runtime validator is implemented by these examples.

| File | Purpose |
| --- | --- |
| [Run manifest](run-manifest.json) | One observe-only evaluation run, fixed baseline and explicit capture/limit scope |
| [Routing policy](routing-policy.json) | Shadow-only catalog, both API and subscription design paths, actuation disabled |
| [Session events](session-events.jsonl) | Retry, duplicate delivery, missing usage, late reconciliation and verified outcome |
| [Task outcome](task-outcome.json) | Artifact-bound acceptance with intervention coverage; inference-only cost scope |
| [Provider request fragments](provider-requests.json) | Actual API field shapes with unresolved model/provider placeholders |
| [Cohort comparison](cohort-comparison.json) | Worked cost/time/autonomy arithmetic on ten fictional tasks per policy |

The policy intentionally has no live-qualified profiles, configured quality floor or exploration.
It is not a ready-to-enable controller configuration. A synthetic recommendation has no authority
to modify the manifest's externally chosen baseline.

## Session/accounting example

The first inference attempt times out without final usage. Its exposure remains held. A second,
separately identifiable attempt succeeds. Event `e07` is delivered twice to illustrate transport
deduplication. The first attempt later reconciles with its own charge.

Correct inference accounting is `0.02 + 0.03 = 0.05 USD`: two charges, not one logical-call charge,
and not `0.08` from counting the duplicate. Before reconciliation, the complete amount is unknown.
The `0.05` is **inference only**, not a complete all-in task cost or a provider API compatibility claim.

For the second attempt, normalized input is 100 tokens, of which 60 are cached. Output is 20,
of which five are reasoning. Input is not 160 and output is not 25. Unknown cache-write usage
remains null rather than being guessed as zero.

The acceptance events bind to the same fictional artifact and explicit complete intervention
coverage. Their assertions exercise the proposed format; no real tests, isolation checks or
human-observation channel ran to establish them.

## Why the cheapest call can lose

The two policies process the same ten synthetic task identities in separate imagined executions.
All costs/outcomes are declared complete for this arithmetic fixture. Human wage costs are
excluded; corrective minutes are reported separately. Request counts include fictional retries.
The p95 uses the nearest-rank definition, not interpolation.

The calculation rejects policies with missing, extra or replaced task IDs; task order may
differ. Absent maturity or intervention-coverage fields keep quality and the cost/success ratio
unknown. This paired-example contract is not a requirement that all real randomized experiments
assign identical task identities to every treatment group.

| Measure | Cheap profile | Balanced profile |
| --- | --- | --- |
| Inference requests | 800 | 400 |
| Mean inference cost/request | $0.05 | $0.15 |
| Total inference | $40 | $60 |
| Sandbox | $20 | $12 |
| Evaluation | $10 | $8 |
| Observability | $2 | $2 |
| All-in cohort cost | $72 | $82 |
| Verified autonomous successes | 6/10 | 9/10 |
| Assisted successes | 2/10 | 0/10 |
| Failures | 2/10 | 1/10 |
| Corrective human minutes | 20 | 0 |
| p95 task wall time | 1,800 s | 600 s |
| Cost/autonomous success | $12.00 | $9.11 |

The balanced profile spends more per request and more on the cohort, yet spends less per
autonomous successful task in this fixture. This illustrates the denominator choice; it does
not establish that a particular model is better, an expected saving, or a statistically reliable
quality floor. Ten fictional tasks cannot qualify a deployment.

Recompute from the Æion Observability project root with standard Python:

```sh
python3 - <<'PY'
import json
from decimal import Decimal
from math import ceil
from pathlib import Path

data = json.loads(Path('examples/cohort-comparison.json').read_text())
assert data['example_only'] is True
for policy in data['policies']:
    tasks = policy['tasks']
    total = sum((Decimal(v) for t in tasks for v in t['costs'].values()), Decimal(0))
    inference = sum((Decimal(t['costs']['inference']) for t in tasks), Decimal(0))
    requests = sum(t['request_count'] for t in tasks)
    successes = sum(t['outcome'] == 'autonomous' for t in tasks)
    durations = sorted(t['wall_seconds'] for t in tasks)
    p95 = durations[ceil(0.95 * len(durations)) - 1]
    per_success = total / successes if successes else None
    print(policy['policy_id'], {
        'cohort_cost_usd': str(total),
        'inference_cost_per_request_usd': str(inference / requests),
        'autonomous_successes': successes,
        'cost_per_autonomous_success_usd': str(per_success),
        'p95_wall_seconds': p95,
    })
PY
```

## Request-fragment limitations

The OpenRouter/DeepInfra bodies use documented Chat Completions field names. Every model,
provider slug and optional variant needs exact capability/price/privacy qualification. No
authentication header is supplied. The optional variant metadata is not a second API schema;
only its explicit body patch belongs in a qualified request.

`reasoning.exclude` in the OpenRouter fragment limits returned content; it does not disable
reasoning cost. DeepInfra's optional tier/cache settings are not universal model capabilities.
Do not send these fragments unchanged through Claude Code's Anthropic-compatible endpoint.
See the [capability matrix](../knowledge/references/provider-capabilities.md).
