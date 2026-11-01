# Changelog

## Unreleased

- Adopt the Æion Factory v1.8.3 template (tag `v1.8.3`, commit `bac6d7b`): `tools/`, `efficiency/`,
  native harness folders, `VERSION`, knowledge policies, merged `AGENTS.md`, the agent adapter check
  and the prompt-defense hook, and the Factory knowledge docs the imported tools name as their spec.
- Verify Pi-to-Langfuse transmission end to end on the local stack, with a local fake model and no
  paid call; the record and the Langfuse v4 read path are in `work/langfuse-pi-plugin.md`.
- Add the fleet view to the cockpit: every run, every tier, one glance, linked to Langfuse.
- Add the high-level architecture diagram (`docs/architecture/`), built with Graphify and Archify,
  and point the committed `tools/architecture/views.json` at this repository's own view.
- Import the Factory `loops/` jobs (orchestrator, prompts, schedules, model routing, Decisions API
  client) that `tools/loops`, `knowledge/operations/loops.md` and `.github/workflows/outer-loop.yml`
  already named, so `tools/factory-tests` passes to the end; ignore `env.local` as Factory does.
- Fix two macOS-only test expectations (a `/private` temporary path and a framework interpreter that
  rewrites `argv[0]`).
