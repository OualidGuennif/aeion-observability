# Phase 3 — Molecules: knowledge bound to code

> *Atoms bind into molecules. Docs bind to the code they describe — and a check notices when one
> moves without the other.*

**In one line:** one canonical knowledge base, one task-state file, docs and code linked both
ways and checked, and a technical-watch folder that keeps the repository's ideas fresh.

> **Agent:** enter plan mode. Map the docs that exist (README, `docs/`, wiki exports, ADRs). Move
> facts into the structure below only where it removes a duplicate or a stale copy; link the rest.

## Why

Docs drift because nothing tells anyone they are wrong. A link costs nothing until it is followed
(Anthropic, *Effective context engineering*: keep lightweight identifiers, load content just in
time), and a deterministic check turns "the doc is probably stale" into a failing line. Research on
doc-to-code trace links finds that naming-based guesses produce most false links; explicit links
remove the guess.

## The structure

```
knowledge/
  index.md            # one table: "to do X, open Y"
  architecture/       # how the parts fit; flows; invariants across components
  components/         # one doc per unit, in the spec format below
  decisions/          # ADRs: context, decision, consequences; superseded, never edited away
  policies/           # durable rules (Phase 1)
  operations/         # build and test, deploy, runbooks, recovery
  references/         # external material still worth keeping (summaries, links)
  current/            # volatile state summaries, each with a stale_after date
work/current.md       # task state only — never knowledge
tech-watch/           # the technical watch (below)
```

**Each concept has a small frontmatter:** `type`, `title`, `description` (at most 250
characters), `status` (draft | stable | deprecated), `generated` (`by`, `at`), `sources` (what the
doc is built from, including the **code files it describes**), and at most three `verified`
entries of at most 300 characters (what was checked, the result, the command or commit). The body
stays under about 600 lines; a longer doc splits along its headings.

**A component doc is a spec**, written before the code changes: *Intent; Data sources; Inputs;
Outputs (every refusal and error); Invariants (each names its test); Determinism (deterministic,
bounded or adaptive, and why); Acceptance checks (commands that pass or fail); Out of scope.*

**`work/current.md`** holds open tasks only, newest first, at most 150 lines, each entry at most 10
lines with five fields: *Owner decision; State; Next (who); Blocker; Evidence.* A finished task is
deleted — the commit message and the knowledge base keep what matters.

## Links both ways, and the check

- **Doc to code:** the doc's `sources` lists the files it describes
  (`resource: ../../src/billing/invoice.ts`). A directory source is checked for existence only.
- **Code to doc:** a file a doc describes carries one header line `Spec: knowledge/<doc>.md`.
- Explicit file paths work independently of language or extension, including spaces and Unicode.
  Header discovery scans the first 8 KiB of leading comments/docstrings in tracked regular text
  files; Markdown, vendored/dependency/cache content, known secrets and symlinks are excluded.
  For formats without comments, use `sources`. This does not install language tools or validate syntax.
- **`tools/knowledge/doc-links`** (shipped with Æion Factory, Python standard library only):
  - **L1** a `Spec:` pointer resolves; **L2** every `sources` path exists;
  - **L3** with `--diff <base>` (`origin/develop`, else `origin/main`): a file changed while a doc covering it did not. Updating the
    doc passes, and so does a commit trailer
    `Docs-Checked: knowledge/<doc>.md -- <why no documented fact changed>`. A diff that only adds or
    removes `Spec:` lines moves no fact and passes.
- Run L1/L2 in the pre-commit, L3 in CI on pull requests, and let the hooks of Phase 5 remind the
  agent at edit time and before it stops.
- **Performance:** a link is a path, not content, so it adds nothing to context until followed; the
  check reads the tree in about a second for a repository of a thousand files.

## The technical watch — this phase creates `tech-watch/`

Create a `tech-watch/` folder in English with:

- `tech-watch/README.md` — the method (copy Æion Factory's): start from current evidence (read
  `AGENTS.md`, the knowledge index, `work/current.md`; record the commit and a cutoff date), form
  findings before reading older reports, search primary sources (official docs, release and
  security notes for the **versions the project actually pins**, papers, credible practitioners),
  open the original behind every post, record date and method, and give each idea one decision:
  *adopt, evaluate, retain, defer or reject*, with its local fit and smallest useful experiment.
  "Nothing worth changing" is a valid result. No new dependency or platform without a shown need.
- `tech-watch/pending/index.md` — how to find pending packages: each watch writes one dated folder
  `tech-watch/pending/YYYY-MM-DD-<topic>/index.md` with a table (ID, priority, state, smallest next
  action, acceptance). Items close as *implemented, already fixed, not applicable, declined* or
  *tracked elsewhere* (with a real destination); when all are closed, the folder is deleted — git is
  the archive.

The outer loop (Phase 6) runs the watch on a schedule.

## Files this phase creates or merges into

`knowledge/**` (index and folder indexes first), `work/current.md`, `tech-watch/README.md`,
`tech-watch/pending/index.md`, `tools/knowledge/{knowledge-check,doc-links}` and their tests.

## Done when

`knowledge-check` and `doc-links` pass; every component that changed recently has a spec; the
README no longer repeats the map or the rules; `work/current.md` holds only open tasks.

## Pitfalls

- A knowledge base that is a journal: dated narratives belong in commit messages.
- `verified` lists that grow forever: three entries, the newest.
- Linking whole directories and expecting the diff check to bite: only exact files count.
