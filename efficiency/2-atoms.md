# Phase 2 — Atoms: code intelligence with native language servers

> *An atom knows its neighbours. An agent with a language server knows where a symbol is defined,
> who calls it, and that the line it just wrote does not compile — before the tests say so.*

**In one line:** register each language's own server with Claude Code, prove it navigates and
reports diagnostics, and keep its data out of the repository.

> **Agent:** enter plan mode. List the languages, their project-local tool versions, and any
> language-server setup that already exists. Reuse a working one; never install a second
> toolchain to match a guide.

## Why

Without a server the agent greps and guesses; with one it gets definitions, references, call
hierarchy and **diagnostics pushed into its context after each edit**, for a few tokens. Claude
Code exposes this as the `LSP` tool plus automatic diagnostics.

## The rules that make it work

1. **One server per file extension.** Claude Code gives each extension to the first enabled
   server; a second one is silently unused. Two servers for `.ts` (Node and Deno, say) means one
   session per scope, not both at once.
2. **The project's own binary, never a global one.** The server must match the compiler the
   build uses: resolve it from the project (`node_modules/.bin`, the repository's JDK).
3. **Native servers first:**

   | Language | Server | Start |
   | --- | --- | --- |
   | TypeScript 7+ | the native compiler | `node_modules/.bin/tsc --lsp --stdio` (TypeScript 7 ships no tsserver; older wrappers do not fit) |
   | TypeScript ≤ 6 | `typescript-language-server` | `typescript-language-server --stdio` |
   | Deno | built in | `deno lsp` |
   | Java | Eclipse JDT LS (Java 21+ to run; compiles 8–25) | its `bin/jdtls` launcher with `--java-executable <the project JDK>` and `-data <a folder outside the repo>` |
   | Python | Pyright | `pyright-langserver --stdio` |
   | Go | gopls | `gopls serve` |
   | Rust | rust-analyzer | `rust-analyzer` |

4. **Server data lives outside the repository.** JDT LS writes Eclipse files (`.project`,
   `.classpath`, `.settings/`) into every module unless the JVM gets
   `-Djava.import.generatesMetadataFilesAtProjectRoot=false` (its launcher's `--jvm-arg=`); the
   initialization option of the same name alone did not stop it with JDT LS 1.63. Put its workspace
   under the user's cache folder, and check `git status` after the first import.
5. **Stdout is the protocol.** A launcher prints nothing on stdout; messages go to stderr.

## How to register them

The smallest supported way is a **local plugin** that contains only the registration:

```
tools/claude-plugins/
  .claude-plugin/marketplace.json      # lists the plugins below
  native-lsp/
    .claude-plugin/plugin.json
    .lsp.json                          # server name -> command, args, extensionToLanguage
    scripts/<launchers>                # resolve the project's binary, then exec it
```

- In `.lsp.json`, `command` and `args` may use `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}`.
  Every field is strict: an unknown key makes the whole file be skipped.
- Add the marketplace and install the plugin at project scope:
  `claude plugin marketplace add ./tools/claude-plugins --scope project` then
  `claude plugin install native-lsp@<marketplace> --scope project`. A marketplace added from a
  local path loads in place, so the launchers stay in the repository.
- `claude plugin validate <dir>` checks the manifest; it does **not** read `.lsp.json`. Look in
  `/plugin` → Errors for `Invalid LSP server config` or `Executable not found`.

The Æion Factory ships this plugin (`tools/claude-plugins/native-lsp`) with launchers for
TypeScript 7, Deno and Java; copy only the servers you need.

## Proving it (each is a separate state: installed, registered, enabled, loaded, working)

1. **Handshake:** the launcher answers an LSP `initialize` with its server name and version.
2. **Navigation, inside Claude Code:** ask the agent to find the definition and the references of
   a real symbol through the `LSP` tool.
3. **Diagnostics:** in a throwaway file, write a deliberate type error; Claude Code must report it
   after the edit, then stop reporting it once fixed. Delete the file.
4. **Persistence:** start a fresh session; the server is still enabled and answers.

If navigation works and diagnostics do not, the result is *partial*: say so.

## Files this phase creates or merges into

| File | Note |
| --- | --- |
| `tools/claude-plugins/**` | only the servers this repository uses |
| `.claude/settings.json` (project scope) | `enabledPlugins` and the local marketplace; written by the CLI |
| `knowledge/operations/build-and-test.md` | a short "Language servers" section: servers, versions, how to switch scopes, how to roll back |

## Done when

Every language in the repository has a working server (or a written reason why not), the four
proofs above passed per server, and no tool data appeared in `git status`.

## Pitfalls

- A registration that points at a global `tsc` or a second JDK: diagnostics then disagree with CI.
- Enabling two servers for the same extension and assuming directory-aware routing.
- Leaving generated IDE files in the tree after a first JDT LS run.
