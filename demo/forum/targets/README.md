# Pinned target profiles

The 100-feature manifest is the canonical [Quarkus/PostgreSQL/React web contract](../ARCHITECTURE.md).
A target profile binds **one** feature to an exact runnable product base and protected check.
Existing 007/013/017 profiles describe the earlier SQLite backend; they do not qualify the
new PostgreSQL migration or React client. The product source is the separate
[`aeion-autonomous-forum`](https://github.com/OualidGuennif/aeion-autonomous-forum) checkout at
`demo/.local/factory/agents/aeion-autonomous-forum`; the files under `demo/forum-app/` are a
reading mirror, not the build source.

`forum-app-013.json` is the historical first profile. `forum-app-017.json` binds strict request validation to a newer exact product base; its external contract rejects missing/unknown/wrong-type fields without values in errors, checks the body cap before authentication and retains valid business refusals. `forum-app-007.json` covers normalized Markdown and safe derived HTML in that existing JSON thread API. Its real external contract checks 30 hostile payloads, exact subset fixtures, stored canonical text and size refusals without an outbox insert. Live dispatch remains subject to current engine, contract and base qualification; a profile's presence alone does not make it launchable. The fixed offline fixture remains 013-only.

Profile fields:

| Field | Meaning |
| --- | --- |
| `base.source` / `base.sha` | the real repository and the exact commit the clone is checked out at |
| `allowed_scope_prefix` | every write scope must stay under this directory |
| `write_paths` | the literal main and test source directories |
| `brief` | the adapted feature brief the worker freezes and copies next to the clone |
| `context_files` (optional) | at most eight regular main Java blobs from the pinned commit; complete public source supplied outside the candidate tree, not host working-tree files |
| `protected_check` | the command, toolchain home, external contract test and timeout |

The brief is limited to 12000 UTF-8 bytes. Optional context accepts only public
`demo/forum-app/src/main/java/.../*.java` paths, up to 24000 bytes per file and 48000 labeled
bytes in total. Symlinks, missing blobs, duplicates, configuration paths and oversized input
are refused when loading the profile, before it can be advertised as ready. No truncated brief
or source excerpt is sent to the author. Context is materialized as controller-owned
`CONTEXT.md` beside `BRIEF.md`, outside candidate write scopes. It is author input, never raw
telemetry. The full review envelope still bounds the complete changed output separately.

For target 013, the base is `37417ab`, the product repository's import commit, before the offline-qualified
feature-013 filter was applied locally (`1224d03`). The worker clones that commit from the
product checkout into `demo/.local/factory/work/<build_id>/repo`, verifies `HEAD` and a clean
tree, and never edits the controller checkout. The pin deliberately stays at the pre-feature
base so the profile keeps proving that a build can produce feature 013; it is not the product's
current `HEAD`.

## What the check proves

Before the protected check, the artifact gate hashes the exact changed bytes and the
deterministic reviewer reads them. The check then copies
`SecurityHeadersContractTest.java` from this directory into the candidate test tree, runs

```text
GRADLE_USER_HOME=demo/.local/gradle-home \
  demo/.local/tools/gradle-9.8.2/bin/gradle -p <clone>/demo/forum-app test \
  --offline --console=plain --no-daemon
```

and restores or removes the contract file. The contract source lives outside both declared
write scopes, so candidate code cannot edit the test that judges it. The check records only
the return code, duration, contract digest and bounded failed-test names.

The test harness (`QuarkusTestDatabase`) is still inside the candidate test scope; a change
to it appears in the reviewed diff, and the deterministic reviewer runs before the check.
Live qualification would add an independent harness copy.

## Run the offline proof

```bash
demo/.local/venv/bin/python demo/tests/qualify_forum_build.py             # emits and reads Langfuse
demo/.local/venv/bin/python demo/tests/qualify_forum_build.py --no-telemetry
```

The builder is an injected fake model: it writes the feature's Java filter and a candidate
test, makes no model call, and costs nothing. The two review votes are injected `approve`
answers; the forge is the fake forge, so no branch, pull request or deployment exists. The
build appears on `/factory` with its ids and trace link. Its store status is
`simulated_complete` because the model and forge are fake, while the Java diff and the Gradle
result are real. The qualification opens the store with `simulated_dependencies=True`: the
runnable app already contains feature 001's skeleton, so that completed dependency is treated
as satisfied.

## Moving the pin

When the forum app changes, update `base.sha` to the new commit and run the unit tests plus
the qualification command. Never point the profile at a moving branch: `load_target` rejects
a base that is not an exact 40-hex commit present in the repository.
