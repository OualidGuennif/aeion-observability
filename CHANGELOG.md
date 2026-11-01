# Changelog

## Unreleased

- Update to the Æion Factory v1.8.4 template (tag `v1.8.4`, commit `fac8bcb`): the dsh web plugin
  tells the shared 250k/300k rule that its profile has no compaction service, so the gate is
  advisory and the harness compacts itself instead of asking for `/compact`; Pi's native compaction
  runs and owes its receipt; `adapter-check` reports a `steer` call without an id as `UNIDENTIFIED`;
  `tools/agents/{connectors.py,refs.py,dsh-install,template-update}` and the `template-update`
  skill arrive, and `tools/factory-tests` runs their suites.
- Adopt the Æion Factory v1.8.3 template (tag `v1.8.3`, commit `bac6d7b`): `tools/`, `efficiency/`,
  native harness folders, `VERSION`, knowledge policies, merged `AGENTS.md`, the agent adapter check
  and the prompt-defense hook, and the Factory knowledge docs the imported tools name as their spec.
- Verify Pi-to-Langfuse transmission end to end on the local stack, with a local fake model and no
  paid call; the record and the Langfuse v4 read path are in `work/langfuse-pi-plugin.md`.
- Add the fleet view to the cockpit: every run, every tier, one glance, linked to Langfuse.
- Add the high-level architecture diagram (`docs/architecture/`), built with Graphify and Archify,
  and point the committed `tools/architecture/views.json` at this repository's own view.
- Split the specification in two: `demo/forum/PLAN.md` is the product (Agora and its 100 app-only
  features), `demo/forum/ECOSYSTEM.md` is the factory that builds it (board, queue, dispatch,
  gates, merge allowlist, observer agent). The 14 factory features that were numbered inside the
  100 are replaced by 14 product features, and the review bundle carries both files.
- Specify Agora, the agent forum, and the build plane that will produce it: `demo/forum/PLAN.md`
  and 100 feature files with a generated manifest and index, plus a verbatim review copy under
  `demo/forum/openAI/`. Specification only; no forum code exists yet.
- Import the Factory `loops/` jobs (orchestrator, prompts, schedules, model routing, Decisions API
  client) that `tools/loops`, `knowledge/operations/loops.md` and `.github/workflows/outer-loop.yml`
  already named, so `tools/factory-tests` passes to the end; ignore `env.local` as Factory does.
- Fix two macOS-only test expectations (a `/private` temporary path and a framework interpreter that
  rewrites `argv[0]`).
