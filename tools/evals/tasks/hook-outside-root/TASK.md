# Task: hook-outside-root

## Starting point

- Commit: `26f19e0` (develop head when this set was written; record the real one in `BASELINE.md`)
- Factory: `1.7.0`
- Branch: `task/hook-outside-root` from that commit

## Prompt (send this text unchanged)

> Add one negative case to `tools/agents/tests/test_hooks.py` for the shared guard's PostToolUse path:
> an edit whose `file_path` resolves outside the repository root is not recorded in the session's
> edited list and does not run `after-edit.py`. Use an isolated session id and a temporary folder so
> the case cannot touch this repository. Then delete the `is_relative_to(root)` branch in
> `tools/agents/hook.py` locally, watch your case fail, restore the branch, and say so in your report.
> Do not change the guard otherwise; no new rule, no new file in `tools/agents/`.

## Scope

- In scope: `tools/agents/tests/test_hooks.py`.
- Out of scope: `tools/agents/hook.py` (restored unchanged by the end), the adapters, any dependency, any push.

## Stop

The run is over when `CHECK.md` passes or you decide it fails; record either outcome.
