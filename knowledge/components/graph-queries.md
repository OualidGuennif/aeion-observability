---
type: Component
title: "Code graph queries"
description: "tools/architecture/ask: a working Graphify graph rebuilt when files change, exact deterministic answers to the structural questions an agent asks before reading code, and type-resolved callers from the project's own language server."
status: draft
generated:
  by: aeion-factory/1.3
  at: 2026-10-28
sources:
  - id: ask
    resource: ../../tools/architecture/ask
    title: "Query command and working-graph rebuild"
  - id: graph
    resource: ../../tools/architecture/graph.py
    title: "Structural extraction and the factory's added edges"
  - id: tests
    resource: ../../tools/architecture/tests/test_ask.py
    title: "Invariant tests"
  - id: skill
    resource: ../../.claude/skills/graph/SKILL.md
    title: "How an agent uses it"
---

# Code graph queries

## Intent
An agent should know where something is, what depends on it, which tests reach it and which spec
covers it before it reads code. Reading whole folders to find out costs tokens and misses links.

`tools/architecture/ask` answers those questions from a Graphify graph of the **working tree**. The
graph is rebuilt only when a project file changed. Every answer is exact, deterministic and names
`file:line`. A call the graph cannot see, a method on an object received as a parameter
(`ideas.create()`), comes from the project's own language server through `callers`, so every harness
gets it, not only those with a language-server tool.

It complements the per-commit baselines of [architecture maintenance](../operations/architecture-maintenance.md),
which stay immutable and feed Archify. Intent and rules still come from `knowledge/` first: see the
`graph` skill.

## Data sources
| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| Project files | `project_files(root, untracked=True)`: git's list, or the plain-folder walk | the project | each call (fingerprint) |
| Graphify 0.9.97 | native AST, Markdown and config extraction; no LLM | `tools/architecture/requirements.txt` | pinned |
| Spec frontmatter `sources`, read from the file on disk (Graphify's cache keys a page by its body) | `specifies` edges, spec → file | knowledge docs | each rebuild |
| `Spec:` comment lines (first 20 lines, the line holds only the pointer, as `doc-links` reads it) | `specified_by` edges, file → spec | each code file | each rebuild |
| Test files' text | `names_file` edges when a test names a project path literally (scripts run as subprocesses) | the tests | each rebuild |
| `deno info --json` | exact `imports` edges of a Deno project, when `deno` and `deno.json` exist | Deno toolchain | each rebuild |
| Language server (`deno lsp`, or the project's TypeScript 7 `tsc --lsp`) | `callers`: call hierarchy, or references when the server has none | the project's toolchain | each call |

## Inputs
`ask [--root DIR] [--json] [--all] <command> [args]`. A name is a file path relative to the root, a
symbol label (`checkpoint_call()`), or a node id.

| Command | Question |
| --- | --- |
| `status` | Is the graph fresh, how big is it, which files yielded no symbol? |
| `find <name>` | Where is it defined? |
| `deps <name>` / `rdeps <name> [--depth N]` | What does it use? What breaks if it changes? |
| `path <A> <B>` | How does A reach B, hop by hop? |
| `tests <file>` | Which tests reach this file, and how? |
| `untested` | Which source files does no test reach? |
| `spec <file>` / `files <spec>` | Which spec covers this file? Which files does this spec cover? |
| `hubs [--top N]` | Where should a newcomer start? |
| `callers <file>:<name or line>` | Who calls this function or method, resolved by type? |

## Outputs
- **Text** (the default) is at most 40 result lines, each with `file:line`. `--all` lifts the cap,
  and a truncated answer says how many lines it hid.
- **`--json`** returns one object: `{"command", "graph": {"fingerprint", "rebuilt", "nodes", "edges"}, "results": [...]}`.
- **Exit codes:**
  - 0: an answer, even an empty one, which is stated;
  - 3: an ambiguous name, with its candidates listed;
  - 4: no node matches;
  - 2: a usage error;
  - 1: the graph cannot be built, for example when the Graphify venv is missing (the message names
    `tools/architecture/setup`); for `callers`, no language server serves the file, or it failed or
    took over 60 s.
- The graph lives in `.aeion/graph/`, which is ignored: `graph.json`, `coverage.json` and `fingerprint`.

## Invariants
| Invariant | Test |
| --- | --- |
| A name matches exactly (path, label, label without `()`, or id). Several matches give exit 3, none gives exit 4, and nothing is guessed. | `test_names_match_exactly` |
| The graph is rebuilt if and only if the files' fingerprint (path, size, mtime) changed. | `test_rebuild_only_on_change` |
| `path` names a hop with no edge instead of skipping it, and prefers imports, then calls. | `test_path_names_each_hop` |
| `tests` and `untested` tell a test that imports a file from one that reaches it through others or names it. | `test_tests_and_untested` |
| `spec` reports each spec from frontmatter and from the `Spec:` comment line; it marks a gap (a code file with no `Spec:` line, or a `Spec:` line the spec's sources omit) and a file shared by two specs, never a conflict. A file no extractor reads still resolves. | `test_spec_both_directions`, `test_real_build_adds_spec_line_and_test_name_edges`, `test_frontmatter_only_edit_updates_spec_sources` |
| `hubs` leaves out tests, documents and external modules. | `test_hubs_exclude_noise` |
| Output order is stable: sorted, never in dictionary order. | `test_output_is_stable` |
| `callers` finds the name exactly in the file (several definitions give exit 3 with their lines, none gives exit 4), picks the server from the nearest `deno.json` or the project's TypeScript 7 install, and exits 1 without installing anything when there is none. | `test_callers_resolve_by_type`, `test_callers_refuse_without_server` |
| `path` with no edge between two files suggests `callers` instead of skipping the hop. | `test_path_names_each_hop` |
| No language model is called. The build is `graph.py` (AST only), and `guard-bash` refuses Graphify's LLM commands. | `test_hooks.py`: graphify LLM commands |

## Determinism
- Same files give the same graph and the same answers. Sorting is by path, then line, then label.
- `deno info` is the only external process of a rebuild, and it is used only for a Deno project. When
  it is missing, `coverage.json` records `toolchain_imports: "unavailable"` and no edge is invented.
- `callers` starts the language server for one question, opens the project's source files, and stops
  the server afterwards. The server reads the files on disk, so the answer is never stale; call sites
  are sorted by path, then line.
- Queries use only the Python standard library on `graph.json`, so a query does not start the venv.

## Acceptance checks
```bash
python3 tools/architecture/tests/test_ask.py
tools/architecture/ask status
tools/architecture/ask rdeps tools/context/budget.py
tools/architecture/ask tests .claude/hooks/guard-bash.py
tools/architecture/ask --root demo/claude_code/workspace callers app/store/ideas.ts:create
```

## Out of scope
- **Type-resolved calls in a language with no server here** (Python: no pyright is installed). `callers`
  says so and installs nothing; the `graph` skill then routes to a search.
- **Type-resolved edges stored in the graph.** A server costs about 2 s per question, too slow for every
  rebuild; `callers` asks it on demand.
- **An MCP server.** A query costs about 50 ms, and a rebuild about 1 s on 155 files. A resident
  server would hold a graph that goes stale as files are edited.
- Graphify's LLM extraction, community labels and SCIP ingestion. SCIP ingestion is an unwired
  skeleton in 0.9.97.

## Skill-level interpretation

Graph results select candidate tests and evidence, not automatic mandatory new tests.
A missing structural edge is not proof of absence or a runtime authorization finding.
The native graph skill now names these boundaries explicitly; query behavior is unchanged.
