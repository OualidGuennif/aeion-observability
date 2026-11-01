# Current work

## Agora forum, and the factory that builds it
- Owner decision: the AI builds the ecosystem around the product — a front where the 100 Markdown features are selected and launched, one or ten at a time — and never writes the forum by hand; agents build the forum from those specs. Requested in chat, 2026-11-01.
- State: the [product plan](../demo/forum/PLAN.md) and 100 app-only feature files are committed; the factory is specified in [ECOSYSTEM.md](../demo/forum/ECOSYSTEM.md). Slice S1 (board, queue, dry-run worker, live view, kill switch) is being built in the cockpit; no forum code exists.
- Next: S1, then S2 — one real Flue build that ends as a draft pull request against a scratch repository.
- Blocker: None; a live build and any paid model call wait for the owner's explicit go.
- Evidence: [plan](../demo/forum/PLAN.md); [factory](../demo/forum/ECOSYSTEM.md); [feature index](../demo/forum/features/README.md); `demo/forum/openAI/` (review bundle).

## Æion Factory v1.8.4 template adoption
- Owner decision: Import AEion Factory (v1.8.2, then v1.8.3, then v1.8.4) and migrate this repository onto its template, then prove Pi sessions reach Langfuse, run Archify/Graphify, and publish a high-level diagram. Requested in chat, 2026-10-31.
- State: Template skeleton imported (tools, efficiency, native harness folders, knowledge policies), AGENTS.md merged with the owner rules, Graphify graph built (1017 nodes), Archify diagram validated and rendered. The local ten-service stack boots from a fresh `demo/.local`, the supervisor's spans and scores reach Langfuse, claude-mem and Hindsight acknowledge, and **Pi → Langfuse via the community plugin was verified end to end, then dropped**: the Flue observer already carries tokens, cache reads and cost, and the plugin's only extra (raw prompts) is what the telemetry policy forbids. The Factory `loops/` jobs are imported and `tools/factory-tests` passes. Updated to v1.8.4 face-for-face through `tools/agents/template-update`: the dsh web plugin no longer stalls a profile without a compaction service, so a session is not held for `/compact`.
- Next: Decide on the Git hooks.
- Blocker: None for the Pi experiment. Langfuse v4 `events_only` removed `GET /api/public/traces|sessions|scores`, so any read-back must use `GET /api/public/v2/observations`.
- Evidence: [repository report](report-2026-11-01.md); [Langfuse + Pi record](langfuse-pi-plugin.md); [high-level diagram](../docs/architecture/high-level.md); `.aeion/analysis/graph-*` (local).

## Flue + Pi execution with OpenShell sandboxes
- Owner decision: Replace the OpenCode CLI and the containerized controller with a Flue + Pi harness in three tiers (just-bash triage, restricted local assistant, isolated autonomous coding), keeping every gate, scenario, memory, telemetry and validation around them. Daytona was rejected after its open-source repository was archived; OpenShell is used through a Flue sandbox adapter instead. Harness² is deferred in favour of deterministic, bounded recovery. The controller runs natively on the host. Approved in chat, 2026-10-27.
- State: [PR #7](https://github.com/OualidGuennif/aeion-observability/pull/7) implements tier 3 and the host-native controller: pinned Flue 2.3.0/Pi 1.4.0, relay-only provider, metadata-only observer, OpenShell adapter and loopback bridge, pre-dispatch admission barrier, stdin-fed checks with a fresh-sandbox verdict, `flue-openshell-v1` method version. Hosted CI qualifies real OpenShell, the four contracts and the real Flue harness (fake inference) on Linux. A second PR adds tier 1 (just-bash triage, one synthetic contract, supervisor verdict, no sandbox) and tier 2 (folder-confined file tools with a strict skill, checks in OpenShell); KPIs and Auto selection key cohorts by tier. Hosted CI qualifies all three tiers on real OpenShell with fake inference.
- Next: Fix the macOS tier-3 transport, then one paid run per tier before any comparison.
- Blocker: On macOS the OpenShell qualification fails: writes on the host-backed work volume are performed but return `EACCES`, so the sandbox reports failure for files that do land. The three tiers pass against a host stand-in (`qualify_flue.py --local-sandbox`) and on Linux CI in a real OpenShell sandbox. No paid run yet.
- Evidence: [validation record](validation.md#flue--pi-harness-with-openshell-sandboxes--2026-10-27); [demo runbook](../demo/README.md); [component](../knowledge/components/docker-demo.md).

## OpenShell isolation and task-specific model lab (historical method)
- Owner decision: Require OpenShell for every build/check execution, disable NVIDIA telemetry, broaden paid Go task/model comparisons, preserve MD-before-reset and 250k/300k gates, retain analyses/decisions in Hindsight. Explicitly approved in chat, most recently 2026-10-27.
- State: The OpenCode CLI campaign (`openshell-go-v5`) completed 40 attempts: 36 accepted outcomes, four retained CLI failures, complete native usage and $0.368068181 in CLI estimates. Published through [PR #4](https://github.com/OualidGuennif/aeion-observability/pull/4); review fixes merged in [PR #5](https://github.com/OualidGuennif/aeion-observability/pull/5) and [PR #6](https://github.com/OualidGuennif/aeion-observability/pull/6).
- Next: None; superseded by the Flue harness. Its cohorts stay historical and never drive Auto selection.
- Blocker: None.
- Evidence: [validation and receipts](validation.md#openshell-migration-and-expanded-model-lab--2026-10-27).
