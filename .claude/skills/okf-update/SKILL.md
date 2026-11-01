---
name: okf-update
description: Updates a knowledge concept after a change - the doc that owns the fact, its spec sections, its links both ways, its frontmatter caps, a verified entry for a check actually run. Use whenever a fact a doc states has changed.
---

# Update a knowledge concept

Format: `knowledge/policies/specs-first.md` and `tools/knowledge/knowledge-check`.

1. Find the doc that owns the fact (`knowledge/index.md`, then the folder index). Change it there; link from elsewhere, never copy.
2. Write it in the body, in the section it belongs to; a Component keeps its eight sections.
3. Frontmatter: `generated.by` and `generated.at`; a `verified` entry only for a check you ran (at most three, 300 characters each; drop the oldest); `description` at most 250 characters.
4. Links: list the files the doc describes in `sources`; give each a `Spec: knowledge/<doc>.md` header line.
5. A new doc goes in its folder's `index.md`.
6. `tools/knowledge/knowledge-check` and `tools/knowledge/doc-links`.
7. Task state goes in `work/current.md`, never in a knowledge doc.

## Keep provenance useful
Record source paths and observed facts in the owning concept; do not copy entire upstream
skills into Knowledge. A source pin/hash proves identity, not successful integration. Distinguish
planned, locally checked and deployed behavior. Remove or qualify stale claims when evidence
changes, and inspect inbound links before renaming or retiring a concept.
