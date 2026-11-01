# CRAFTED — seven useful habits for coding agents

CRAFTED is Æion's mnemonic for the existing seven phases. It is a practical guide, not an
established external standard or a promise of autonomous correctness.

| | Principle | Phase | A concrete starting point |
| --- | --- | --- | --- |
| C | **Clarify the context.** | [Quarks](1-quarks.md) | A short AGENTS.md with purpose, boundaries and verification commands. |
| R | **Read the actual code.** | [Atoms](2-atoms.md) | Follow a definition, inspect callers, then verify project diagnostics. |
| A | **Anchor docs to code.** | [Molecules](3-molecules.md) | A source pointer that tools/knowledge/doc-links can resolve. |
| F | **Follow proven procedures.** | [Cells](4-cells.md) | One focused skill for a task that actually repeats. |
| T | **Turn checks into reflexes.** | [Organisms](5-organisms.md) | A hook near the edit and the same relevant check in CI. |
| E | **Examine every change.** | [Constellations](6-constellations.md) | A branch, a real diff, independent review and current CI evidence. |
| D | **Document the evidence.** | [Galaxy](7-galaxy.md) | A sourced decision or a verified lesson for the next session. |

## Try the core checks

Run these from an Æion Factory checkout with Python 3 available:

~~~sh
tools/knowledge/knowledge-check
tools/knowledge/doc-links
tools/repo-health/repo-health
~~~

They check document structure, links and repository size limits. They do not prove every written
claim or replace the application's tests, review and production safeguards.

For an existing repository, its instructions win. Apply one chapter at a time, with an approved
plan and a reviewable change. Optional loops, external memory and APIs are not prerequisites.
