---
name: graph
description: Knows the code's structure before reading it - knowledge/ for intent, then tools/architecture/ask for exact, deterministic answers (where a symbol is defined, what depends on a file, how A reaches B, which tests and spec cover it), then the language server, then targeted reads. Use before changing code, when tracing a flow, when choosing tests to run, or when exploring an unfamiliar area. No language model is involved.
---

# Know before you read

Reading folders to find out how code fits together costs tokens and misses links. Ask first, then
read only the lines the answers name. Spec: `knowledge/components/graph-queries.md`.

## Order
1. **Intent and rules: `knowledge/`.** Read `knowledge/index.md`, then the doc of the area. The graph
   says what *is*; the docs say what *should be* and why.
2. **Structure: `tools/architecture/ask`.** The graph of the working tree is rebuilt only when a file
   changed (about 1–2 s), and a query on a fresh graph takes about 0.1 s. Every line names `file:line`.
3. **Type-resolved references: the language server.** A method called on an object received as a
   parameter (`ideas.create()`) has no edge in the graph. `ask callers <file>:<name or line>` asks the
   project's own server (`deno lsp`, or a TypeScript 7 `tsc --lsp`) in any harness; then the LSP tool
   (`findReferences`, `incomingCalls`) where the harness has one; without either, `rg -n '\bcreate\('`
   limited to the folder the graph named.
4. **Targeted reads.** Open only the lines the answers named, with an offset and a limit.

## Question → command
| Question | Command |
| --- | --- |
| Is the graph fresh? What did it miss? | `ask status` |
| Where is it defined? | `ask find <name>` |
| What does this file or symbol use? | `ask deps <path or name>` |
| What breaks if I change it? | `ask rdeps <path> --depth 2` |
| How does a request reach the store? | `ask path <from> <to>` |
| Who calls this method, resolved by type? | `ask callers <file>:<name or line>` |
| Which tests do I run after this change? | `ask tests <path>` |
| What is not tested at all? | `ask untested` |
| Which spec do I update? Which files does this spec cover? | `ask spec <path>`, `ask files <doc>` |
| Where should I start in this codebase? | `ask hubs --top 10` |

The commands run from the project root; `--root <dir>` points at another project (a demo workspace),
`--json` gives one object for scripts, `--all` lifts the 40-line cap.

Example, on the factory itself:
```text
$ tools/architecture/ask rdeps tools/context/budget.py --depth 2
.claude/hooks/context-budget.py  [imports_from at .claude/hooks/context-budget.py:11]  depth 1
tools/agents/hook.py  [imports at tools/agents/hook.py:15]  depth 1
tools/context/tests/test_budget.py  [names_file at tools/context/tests/test_budget.py:272]  depth 1
tools/agents/tests/test_hooks.py  [names_file at tools/agents/tests/test_hooks.py:15] via tools/agents/hook.py  depth 2
```

## Before a change
1. `ask rdeps <file> --depth 2`: the impact. Each caller you will touch gets a targeted read.
2. `ask tests <file>`: the exact tests to run, `direct` first; `named` means the test runs the file as
   a script. No test listed: inspect the owning tests and decide whether meaningful regression coverage is needed (skill `test`).
3. `ask spec <file>`: the doc to update in the same change (skill `okf-update`). `frontmatter only` or
   `Spec: line only` is a contract half written: fix the missing side.

## Rules
- **Verify before you claim.** Open each hop's `file:line` before you state a flow in an answer, a
  plan or a commit.
- **Say where the graph is silent.** "No edge path" means imports and calls do not connect the two
  files; the link may be a method on an object, a route string, a subprocess or configuration. Name
  which, after checking with the language server or a search.
- **Exit codes mean something.** 3: the name is ambiguous; choose one of the listed ids. 4: no node has
  that exact name; use `find`, or check the spelling against the file. Nothing is guessed.
- **No model.** Never run `graphify extract`, `label`, `provider`, `add`, `clone`, `global`, an
  installer, or `cluster-only` without `--no-label`: the Bash guard refuses them. The committed
  architecture baseline stays with `tools/architecture/refresh`.

## Known failures
| Symptom | Cause | What to do |
| --- | --- | --- |
| exit 1, "the Graphify venv is missing" | analysis integrations not installed | ask the user, then `tools/architecture/setup` (it installs a venv in `.aeion/`) |
| `status` lists a file under "no symbol" | top-level script without functions, or no extractor | read it directly; it is small |
| a test you know exists is missing from `ask tests` | it reaches the file through a string or a fixture | search the test folder for the file's name; consider naming the path literally |
| `toolchain imports: unavailable` | `deno` is not on PATH in a Deno project | Graphify's own imports remain; install nothing, say so |
| an inferred call is missing | Graphify matched a call by name, with no import between the files | `ask` drops those on purpose; use `ask callers` |
| `callers` exit 1, "no language server" | no `deno.json` and no TypeScript 7 in `node_modules` (Python, plain JS) | install nothing; use the `rg` search the message gives |

## Verification
- [ ] Each structural claim cites a `file:line` you opened.
- [ ] The tests `ask tests` listed ran, and their result is stated.
- [ ] The spec `ask spec` named is updated, or the change does not touch what it states.

## Bounds of graph evidence
Choose tests for actual behavioral risk even if the graph has no direct test edge; a prose-only
change does not require a new implementation-mirroring test. A dependency edge does not prove
a route is reachable, authorized or executed in production. Verify the relevant hop in code
and configuration before turning an inferred path into a review finding.
