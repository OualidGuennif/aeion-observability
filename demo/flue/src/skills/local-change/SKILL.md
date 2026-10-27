---
name: local-change
description: Strict procedure for one supervised change to src/pricing.js in a local workspace. Use before any other action on a local-assistant task.
---

Follow these steps in order. Do not skip, reorder or add steps.

1. If the user message contains a handover, treat it as the current state of the task.
2. Read `src/pricing.js`. If it does not exist, continue with an empty file.
3. Write the complete implementation to `src/pricing.js` with the `write` tool, or apply a
   targeted change with the `edit` tool. Touch no other file.
4. Read `src/pricing.js` again and compare it with every rule of the task contract.
5. Fix any mismatch with `edit`, then stop and reply with one short sentence.

Constraints:

- Only `src/` is writable; the workspace has no shell, network or test runner.
- Do not add imports, other files or tests.
- Protected checks run after you stop; your reply does not decide acceptance.
