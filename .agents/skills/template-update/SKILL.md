---
name: template-update
description: Updates a project that adopted Æion Factory to a newer release - finds the release it came from, reads the release notes and major-version changes, updates every factory file the project left untouched, merges the ones it edited, and hands the project's own instructions, settings, knowledge and conflicts to a human with a proposal for each. Use when an adopted project should follow a new factory release, or when its connectors drifted from a release.
---

# Update an adopted project to a new release

The project's own text wins. A connector belongs to the factory; everything the project wrote
belongs to the project; a factory file the project edited belongs to both and is merged. The whole
skill is keeping those three apart, and saying what the release changes for this project.

## File classes

| Class | Files | Rule |
| --- | --- | --- |
| Contract | `CONTRACT` in `tools/agents/connectors.py`: adapters, hooks, plugins, native registrations | **The factory wins, byte for byte.** Never hand-merge one: a difference is the bug. |
| Merge | `AGENTS.md`, `.claude/settings.json`, `.codex/config.toml`, `.devin/config.json` | **The project wins.** The factory's change arrives as a proposal you apply by hand. |
| Project-owned | `VERSION`, `CHANGELOG.md`, `.aeion-factory`, `work/`, `knowledge/`, `demo/` | **Never written.** A changed factory `knowledge/` doc is listed for review. |
| Three-way | every other factory file: git hooks, skills, tools, CI, guides, README | Untouched since the baseline, or still an older release's exact copy (`untouched since <tag>`): takes the release. Edited: merged with `git merge-file`. Conflict: kept as it is, with a proposal. Deleted by the project: stays deleted. |

## Steps

1. **Prepare.** Run the tool from the factory checkout with the target fetched (`git fetch --tags`),
   never the project's own copy, which cannot see the new release. Make sure the project's tree is
   committed: a write refuses tracked changes, so the update is one revertible commit.
2. **Preview.** Run `tools/agents/template-update --ref <tag> --root <project> --check`. Read:
   - the header's baseline and how it was found. `.aeion-factory` and `--from-ref` are facts; an
     `inferred` baseline is a guess. If it is partial (fewer connectors than all match), ask the owner
     which release the project adopted and pass it as `--from-ref`. Never take it from `VERSION`:
     an application's `0.1.0` is not factory `0.1.0`.
   - the `MAJOR` banner and the release notes: bold lines are actions for existing projects.
   - the groups: `DRIFT`/`MODE` connectors, `UPDATED`/`ADDED`/`REMOVED`/`MERGED`, `CONFLICT`,
     `REVIEW`, `merge`, `review` (knowledge), `migrate`.
3. **Stop and ask.** In a few lines, tell the owner what the release changes for this project (from
   the notes and the major banner), which files need a human (conflicts, merges, reviews), what you
   propose for each, and every `migrate` line. Wait for a yes.
4. **Write.** Run the same command without `--check`. Proposals land in
   `.aeion/template-update/<ref>/` (ignored by its own `.gitignore`); `.aeion-factory` now records the target, so
   resolve every conflict before the commit: the next update starts from that target.
5. **Resolve, one file at a time.**
   - `conflict`: compare the project's file with its proposal (`diff <file>
     .aeion/template-update/<ref>/<file>`), keep the project's intent, take the factory's fix,
     remove every marker.
   - `merge` (`AGENTS.md`, settings): add the factory's new rules or keys where they do not
     contradict the project's; keep the project's wording, build commands and order.
   - `review`: read the factory diff the output names; change the project's doc only when a fact it
     states is now wrong, and say so.
   - `migrate`: show the owner the command. The owner runs it; `aeion.mode` in particular is
     refused to the agent.
6. **Verify.** `tools/agents/adapter-check --root <project> --ref <tag>` is PASS; the project's own
   checks and tests pass (`tools/knowledge/doc-links`, `tools/factory-tests` or its build); no
   conflict marker remains (`git grep -n '^<<<<<<< project'` finds nothing); `VERSION` is unchanged;
   a new session's start line shows the expected mode.
7. **Commit** as one change, `chore: update Æion Factory to <tag>`, listing what was merged by hand
   and why. Do not tag, push or open a pull request unless asked.

## What this must never do

- Rewrite `AGENTS.md`, `knowledge/`, `work/`, `CHANGELOG.md`, `VERSION` or a merged settings file
  without the owner's yes on that file.
- Resolve a conflict by taking the factory's side wholesale, or by deleting the project's lines.
- Improve, tidy or modernise the project's own instructions during an update.
- Write on a guessed baseline: a partial inference is `--check` only until `--from-ref` confirms it.
- Run a migration step for the owner, such as `git config aeion.mode team`.
- Write through a symlinked file or parent; the update refuses the whole set before writing anything.
- Leave a contract file half-matched; a copy that differs from the reference is the failure the
  update exists to remove.
- Recreate a file or folder the project deliberately removed.

## When the factory and the project disagree

The project's approach wins on anything it authored: its task shape, its build commands, its
policies, its domain specs. The factory wins on the files a harness loads, because a hand edit
there fails silently in the harness rather than in review. If a factory change makes the project's
own content wrong, propose the correction separately, with the evidence, instead of folding it into
the update.

## Branch references and several releases

`main` and `develop` are valid for `--from-ref` and `--ref`; the marker records the commit, so the
next update starts from what the project actually took. Several releases at once are one update:
the notes cover every release crossed, and each `migrate` line is for one of them. Prefer tags for
anything the project will keep.
