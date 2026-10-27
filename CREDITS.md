# Credits and attribution

Æion Observability combines existing standards, tooling and research. The proposed task/outcome
contracts and control requirements are Æion's synthesis; errors in that synthesis are ours.
No upstream project endorses this work, and no product/research performance claim is adopted
as a measured Æion result.

- **OpenTelemetry and its contributors** — OTLP, Collector, semantic conventions, GenAI signals,
  security and resilience guidance. [Project](https://opentelemetry.io/),
  [GenAI specification](https://github.com/open-telemetry/semantic-conventions-genai).
- **Anthropic and Claude Code/Agent SDK contributors** — native telemetry, model/effort controls,
  agent-evaluation practice and infrastructure-noise research. [Documentation](https://code.claude.com/docs),
  [agent evaluations](https://www.anthropic.com/research/demystifying-evals-for-ai-agents).
- **OpenRouter and DeepInfra** — official routing, parameter, usage, interoperability and privacy
  documentation. [OpenRouter](https://openrouter.ai/docs), [DeepInfra](https://docs.deepinfra.com/).
- **Langfuse/ClickHouse, Arize/OpenInference/Phoenix, OpenLIT, MLflow, LiteLLM, vLLM Semantic Router,
  New Relic and Modal contributors** — documented observation, evaluation and operational patterns.
  Their separate licenses and feature boundaries are identified in the source register.
- **Research authors** — Chen, Zaharia and Zou (FrugalGPT); Ong and coauthors (RouteLLM); Hu and
  coauthors (RouterBench); Poon and coauthors (online LLM selection); Son, Yoon, Tang, Wang,
  Wolf and Bogunovic (SWE-Router);
  Raj, Kundu, Joshi and Krishna (ORACLE); Li, Gao and Lakshmanan (WISERouter); Paul and Nandy
  (AgentRouter); Dudík, Langford and Li (doubly robust evaluation); Howard, Ramdas, McAuliffe
  and Sekhon (confidence sequences). See the [papers and reading scope](knowledge/references/sources.md).
- **Æion Factory and contributors** — the fixed development foundation, CRAFTED, specification
  structure and evidence-led workflow. [Repository](https://github.com/OualidGuennif/aeion-factory).
- **Flue (withastro) and Pi (earendil-works) contributors** — the pinned agent harness
  (`@flue/runtime`/`@flue/cli` 2.3.0, Apache-2.0) and its model/agent core (`@earendil-works/pi-ai`
  1.4.0, MIT) used by the local showcase. [Flue](https://github.com/withastro/flue),
  [Pi](https://www.npmjs.com/package/@earendil-works/pi-ai).
- **just-bash (vercel-labs) and Valibot contributors** — the emulated in-memory shell behind the
  triage tier (`just-bash` 3.6.0, Apache-2.0) and the schema library for its submission tool
  (`valibot` 1.5.0, MIT). [just-bash](https://github.com/vercel-labs/just-bash),
  [Valibot](https://github.com/open-circle/valibot).
- **OpenCode, Deno and Hono contributors** — the Go inference service and its documentation
  (the OpenCode CLI powered the earlier `openshell-go-v5` evidence), the JavaScript runtime,
  native OpenTelemetry support and small application API used by the local showcase.
  [OpenCode Go](https://opencode.ai/docs/go/), [Deno](https://docs.deno.com/), [Hono](https://hono.dev/).
- **Vectorize/Hindsight and thedotmack/claude-mem contributors** — local semantic session
  memory and the explicit working-memory save/read API.
  [Hindsight](https://github.com/vectorize-io/hindsight), [claude-mem](https://github.com/thedotmack/claude-mem).
- **Z.ai, DeepSeek and MiniMax** — official tokenizer/chat-template files fetched at pinned revisions
  and checked against [fingerprints](demo/tokenizers.json). They are fetched with their license
  files into the ignored `demo/tokenizers/` folder by `demo/install.py`. No coding-model weights are bundled.
- **Manrope and Cormorant Garamond authors** — local font assets, with their OFL notices in
  `demo/app/fonts/`. The showcase illustration was generated natively with GPT Image for Æion;
  it is decorative artwork, not a measured architecture or runtime result.
- **The CROA Project — Yasmine Durand, Darrin Smith and Sylvain Durand** — Constrained Reachability
  Orchestration Architecture, governance boundaries and durable evidence principles.
  [Website](https://www.croaframework.org/),
  [official repository v1.0.1](https://github.com/CROA-Project/CROA/tree/v1.0.1),
  [white paper DOI](https://doi.org/10.5281/zenodo.22310276).
  CROA prose retains CC BY 4.0 and upstream code/schemas their Apache-2.0 terms. No original
  CROA implementation/schema is bundled here. This work does not claim CROA certification.
  [Æion's separate audit adaptation](https://github.com/OualidGuennif/aeion-croa) preserves its own
  explicit attribution and licensing.

Original material authored for this folder is covered by [its MIT license](LICENSE). Linked
documentation, software, papers, names and trademarks retain their respective rights/licenses.
Source fingerprints identify consulted material; full upstream pages are not republished here.

- **NVIDIA OpenShell contributors** — mandatory sandbox gateway, policy enforcement and SDK,
  version 0.1.5. [Release](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.5),
  [telemetry opt-out](https://docs.nvidia.com/openshell/v0.1.5/observability/telemetry/),
  [runtimes](https://docs.nvidia.com/openshell/v0.1.5/how-it-works/sandboxes/runtimes/).
- **models.dev contributors** — the public OpenCode Go catalog subset used by the earlier
  OpenCode harness evidence, retrieved 2026-10-26 from [the catalog](https://models.dev/api.json).
  The current profiles carry their own Go prices and limits; neither is an account entitlement check.
