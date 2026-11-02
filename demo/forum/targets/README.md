# Pinned target profiles

The 100-feature manifest remains the canonical plan and still points at the planned
`demo/forum/product/` tree. A target profile binds **one** catalog feature to the runnable
forum without rewriting the other 99 specs. The product source is the separate
[`aeion-autonomous-forum`](https://github.com/OualidGuennif/aeion-autonomous-forum) checkout at
`demo/.local/factory/agents/aeion-autonomous-forum`; the files under `demo/forum-app/` are a
reading mirror, not the build source.

`forum-app-013.json` is the first profile:

| Field | Meaning |
| --- | --- |
| `base.source` / `base.sha` | the real repository and the exact commit the clone is checked out at |
| `allowed_scope_prefix` | every write scope must stay under this directory |
| `write_paths` | the literal main and test source directories |
| `brief` | the adapted feature brief the worker freezes and copies next to the clone |
| `protected_check` | the command, toolchain home, external contract test and timeout |

The base is `37417ab`, the product repository's import commit, before the offline-qualified
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
