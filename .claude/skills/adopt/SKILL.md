---
name: adopt
description: Applies the Æion efficiency guide to an existing repository one phase at a time, in plan mode, merging into what the repository already has and never overwriting it. Use when bringing an existing repository to this setup.
---

# Adopt the guide in an existing repository

1. Read `efficiency/00-EFFICIENCY.md` (the four promises: harmless, plan first, evidence, no over-engineering).
2. Inventory the repository's own instructions, docs, hooks, CI and conventions: they win.
3. Pick the next phase (1 to 7) and read its chapter; plan the smallest change that fits; list what you keep as is and why.
4. Wait for a yes; implement on a branch; run the phase's "Done when" checks.
   Before the first managed task, adapt `knowledge/components/factory-architecture.md` and
   `tools/architecture/` scope/views to the actual project. Recommend the Graphify/Archify baseline
   strongly, say what `tools/architecture/setup` installs, ask whether this is a work computer, and
   run it only on a yes; CI analyses every main update either way.
5. Open a PR (skill `sign-off`, then `pr-review`). One phase per PR.

Read the README runtime matrix before setup. Preserve the original Claude integration; load
Codex project/hook trust and shared skills through .agents, the local OpenCode plugin/config, or the Pi extension in .pi/.
Verify native discovery/denial behavior. A folder existing is not proof that callbacks are loaded.

## Preserve native integration boundaries
Confirm which host discovers skills and which hooks it actually trusts. Shared skill links
should resolve to one maintained definition; do not copy a second policy set per harness.
If the project-local skills pool is present, use its files as optional guidance only, never register
hundreds of source skills or agent profiles globally. A missing pool must not break adoption.

Run a harmless allowed action and a safe refused fixture through the available native adapter
when authorized; otherwise qualify only the static configuration. Keep an inventory of retained
owner rules and the exact edits needed for this repository, not a blanket upstream scaffold.
