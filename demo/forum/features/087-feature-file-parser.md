---
id: 087
title: "Feature file parser"
area: build
size: M
parallel: true
depends_on: []
owner: builder
status: proposed
---

# 087 — Feature file parser

**Goal.** Read one feature file into a typed record — frontmatter plus the four prose sections — and refuse a file that is missing any of them.

## Scope

- A parser for the exact frontmatter keys this contract uses, with no YAML dependency.
- Section extraction by heading, with a refusal on duplicate or missing headings.
- A `--check` mode that validates every file in `features/`.

## Out of scope

- A general Markdown parser or a metadata database.
- Editing features from the interface.

## Acceptance

- [ ] Every generated feature parses to a record with all fields non-empty.
- [ ] A file missing Acceptance is refused with its path.
- [ ] A frontmatter key outside the contract is refused, not ignored.

## Security

The parser reads files only; it never executes or evaluates their content.

## Test

Parse the 100 files, then a set of truncated and malformed ones.
