---
type: Policy
title: "Specs first, and links to code"
description: "The eight spec sections a component doc carries, the determinism slider, and the links between docs and code that tools/knowledge/doc-links checks."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: tool
    resource: ../../tools/knowledge/doc-links
    title: "The link checker"
  - resource: ../../tools/knowledge/knowledge-check
    title: "knowledge-check, which names this doc as its spec"
---

# Specs first

The spec is the source of truth; the code implements it. A component doc, and any new feature
before its code is written, has these sections in this order:

```markdown
## Intent              one or two sentences: what it is for, which decision it serves
## Data sources        | Source | What is read | Owner | Freshness |
## Inputs              exact structure: types, fields, units, allowed values; a link to the type
## Outputs             exact structure, plus every refusal and error code
## Invariants          numbered; each names the test that proves it
## Determinism         deterministic | bounded | adaptive, and why
## Acceptance checks   commands that pass or fail
## Out of scope        what it does not do, one line each
```

| Level | Who produces the output | How it is checked |
| --- | --- | --- |
| deterministic | code | unit and parity tests |
| bounded | a model, under a fixed output contract | a strict parser; unreadable output is a refusal |
| adaptive | a model, free text | never an authority: advice or a report |

# Links between docs and code

- **Datation:** a volatile document may carry `review_after: YYYY-MM-DD` in its frontmatter;
  `tools/knowledge/stale` fails once the date passed, and a document without the key is exempt.
  A present key must hold a real, nonempty date; a blank value is invalid, not an exemption.
- **Doc to code:** the doc's frontmatter `sources` lists the files it describes
  (`resource: ../../src/area/file.ts`). A directory source is checked for existence only.
- **Code to doc:** a described file carries one header line `Spec: knowledge/<doc>.md`, and that doc
  lists the file (or a folder holding it) in its `sources`: the contract runs both ways (L4).
- `tools/knowledge/doc-links` fails when a pointer or a source does not resolve, when a `Spec:` doc's
  sources omit the file that names it, and with
  `--diff origin/develop` (or `origin/main` without develop) when a file changed while a doc covering it did not. Updating the doc, or a
  commit trailer `Docs-Checked: knowledge/<doc>.md -- <why no documented fact changed>`, passes.
- A link is a pointer, never copied content.
- Git enumeration, history and diff failures return nonzero with a short diagnostic. An unreadable
  repository (a `.git` git cannot read) or missing comparison base is not an empty change set and
  never produces PASS. A plain folder without git is walked from disk (L1, L2 and L4; `--diff` needs git).
- A project nested in this one (a folder with its own `AGENTS.md` and `knowledge/index.md`, such as a
  demo copy) owns its `Spec:` pointers: they name its own `knowledge/`, so this root skips its files
  in L1 and L3, and the nested project's own `doc-links` checks them.
- Paths are read from Git (or the disk walk) verbatim, including spaces and Unicode. Explicit relative `sources`
  work for any file format; only a path beginning with `./` or `../` may contain whitespace.
- Header discovery reads at most 8 KiB of leading comments/docstrings in tracked regular UTF-8
  text files, regardless of suffix. It excludes Markdown, `knowledge/`, vendored/dependency/cache
  folders and secret paths (the shared list in `.claude/hooks/secret_names.py`). It never follows
  file symlinks. Use explicit sources for other formats or metadata after executable code;
  directory sources remain existence-only.
- A documentation-only exemption accepts standalone comment `Spec:` lines and blanks, never
  executable code that happens to contain a pointer.

Diff coverage retains bounded `Spec:` headers from the merge base for deleted files and removed
pointers. Removing an implementation/header does not silently remove its documentation duty.
`Docs-Checked` exemptions require the complete `Docs-Checked: knowledge/<doc>.md -- <reason>`
line with a nonempty explanation; review still verifies whether that explanation is truthful.
