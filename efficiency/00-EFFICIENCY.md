# Æion Efficiency — turn any repository into a calm, self-checking machine for coding agents

> **For the agent reading this file:** you are about to change how a repository works.
> **Enter plan mode first.** Read this file, then the chapter you are asked to apply, then the
> repository. Propose a plan; change nothing until a human approves it.

This guide has seven phases, from the smallest particles to a galaxy. Each phase is useful on its
own, each builds on the one before, and none needs the others to be finished. Apply one at a time.

| Phase | Chapter | One line |
| --- | --- | --- |
| 1 | [Quarks](1-quarks.md) | The rules everything is made of: a short `AGENTS.md`, policies, security, a tidy tree |
| 2 | [Atoms](2-atoms.md) | Code intelligence: native language servers, so the agent navigates instead of guessing |
| 3 | [Molecules](3-molecules.md) | Knowledge bound to code: docs, task state and links checked both ways; a tech-watch folder |
| 4 | [Cells](4-cells.md) | Skills: the procedures you repeat, written once, loaded only when needed |
| 5 | [Organisms](5-organisms.md) | Hooks: reflexes that check every edit, refuse secrets, and sign off every task |
| 6 | [Constellations](6-constellations.md) | Loops: inner (the session), middle (branch, PR, review), outer (scheduled, read-only) |
| 7 | [Galaxy](7-galaxy.md) | Memory and decisions: session retros, taste, a Decisions API; the system improves itself |

The goal is **small context, fast feedback and verifiable changes**. Automated checks reduce
routine review work; independent review and human decisions still matter. The seven habits have
a short name: [CRAFTED](CRAFTED.md).

## The four promises (read these before anything else)

1. **Harmless.** Nothing here overwrites what a repository already has. An existing `AGENTS.md`,
   `CLAUDE.md`, policy, hook, skill, CI job or convention **wins** over this guide. When they
   conflict, keep theirs and note the difference; when they overlap, merge into theirs.
2. **Plan first.** Every phase starts in plan mode: inspect, then propose the smallest change that
   fits the repository, then wait for a human's yes.
3. **Evidence, not claims.** A phase is done when its checks pass, not when files exist. Installed,
   configured, enabled and working are four different states; report each.
4. **No over-engineering.** Add a file, a tool or a rule only when it removes a real, repeated
   cost. Deleting a useless doc is progress.

## How to use it

- **An existing repository:** give your agent this file and one chapter at a time, in order:
  *"Read efficiency/00-EFFICIENCY.md and efficiency/1-quarks.md, then plan phase 1 for this repo."*
- **A new repository:** copy the whole Æion Factory as a starting point (its `README.md` says how)
  and walk the phases to adapt it.
- **Every phase ends the same way:** checks run, results reported, docs and task state updated,
  one pull request, one review comment.

## Assumptions

- Claude Code, local Codex, OpenCode and Pi share instructions, Knowledge and maintained skills.
  Native hooks/configuration differ; follow each setup in Æion Factory README and compatibility
  runbook. Claude plugins remain Claude-specific; token guarantees are not assumed portable.
- A git repository on a forge with pull requests (GitHub examples; others work the same way).
- Nothing in this guide needs a paid service beyond the agent itself; optional integrations
  (a Decisions API, a memory service) stay **off** until someone turns them on.

## Credits

The ideas here stand on other people's work; see the [credits](../CREDITS.md). In particular the
skill anatomy follows Addy Osmani's `agent-skills` (MIT), and the hook, security and skill tooling
comes from Anthropic's official Claude Code plugins.
