# Droid (factory.ai) configuration for Æion Factory

This folder belongs to Factory's Droid CLI, a separate product from Æion Factory. Only
`settings.json` and this file are tracked: its hooks send Droid's events to the shared Æion Factory
adapter, `tools/agents/hook.py droid`. Droid reads `AGENTS.md` and `.agents/skills` natively.

Æion Factory's own local state (analysis, context, loop bodies) lives in the ignored `.aeion/`.
A clone that kept it here keeps its Graphify/Archify baseline by moving it once:
`mkdir -p .aeion && mv .factory/integrations .factory/analysis .aeion/` (add `.factory/opencode`
for an `--isolated` OpenCode profile). The other old folders are disposable.
Contract and qualification steps: [agent compatibility](../knowledge/operations/agent-compatibility.md).
