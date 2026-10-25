# Æion Observability

This is a research/design workspace with an opt-in local Docker demo. Read [README](README.md) and the
[framework](knowledge/components/observability.md) before extending it.

## Working rules

- Keep code, documentation and examples in English; communicate with the owner in French.
- Keep Factory as the development foundation. Do not alter sibling projects for this research.
- Separate verified upstream behavior, Æion requirements, hypotheses and measured results.
- Use primary sources and dated/pinned references. Search results alone do not prove behavior.
- Proposed JSON keys in examples are Æion design fields unless explicitly marked provider API.
- Keep both subscription-token and API paths. Never claim an API control exists in the CLI
  without checking the actual harness/version and protocol.
- Do not install telemetry plugins, inspect transcripts/credentials, export user data, deploy
  a backend, or spend on model evaluations merely to update the research.
- No raw prompts, source, hidden reasoning, tool payloads or secrets in default telemetry.
- Observability may recommend model settings; it cannot expand OPS/CROA permissions or remove
  Factory review gates. Workload events are untrusted evidence.
- Prefer a small catalog of tested profiles over automatic tuning of every parameter.
- Synthetic examples are not benchmark evidence. Preserve their explicit synthetic labels.
- Follow Factory's eight-section component spec and concise current-work format.

## Validation

Standalone checks from this checkout:

```sh
python3 examples/compare_cohorts.py
python3 examples/validate_fixtures.py
python3 -m unittest discover -s tests -v
node --test demo/tests/gate.test.mjs
python3 -m unittest discover -s demo/tests -v
```

Optional documentation checks in a workspace that also contains Factory:

```sh
Æion_Factory/tools/knowledge/knowledge-check --root "$PWD/Æion_Observability"
Æion_Factory/tools/knowledge/doc-links --root "$PWD/Æion_Observability"
```

Validate JSON examples and their cross-references before reporting them as checked.
Do not claim provider, runtime, privacy or controller qualification from document checks.
The Docker pilot has separate CLI and backend checks in [demo/README.md](demo/README.md).
Do not print its private environment file, raw CLI output or credentials.
