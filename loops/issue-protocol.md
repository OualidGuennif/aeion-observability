# Issue protocol

How the loops hand work to each other, through the forge's issues.

| Label | Meaning |
| --- | --- |
| `loop:outer` | opened by an outer-loop job (health, docs, security, watch) |
| `severity:high` / `severity:medium` / `severity:low` | from the finding; `high` routes the fix to the most capable model |
| `agent-ready` | the fix is clear, small and needs no human decision: an inner run may take it |
| `needs-owner` | a decision, a deploy, a cost or a policy is involved: a human first |

- **One finding, one issue.** Title: the rule or symptom; body: where (file:line or the read that
  failed), the evidence, the smallest fix, how to verify. Never a secret, never exploit detail
  beyond what the fix needs.
- **Before opening, search** the open issues with `loop:outer`; comment on an existing one instead
  of duplicating it.
- **An inner run takes one `agent-ready` issue** (`loops/orchestrator.sh inner --issue N`): branch,
  pull request "Fixes #N", review comment, merge after green CI.
- **A human can promote** an issue to `agent-ready` or demote it to `needs-owner` at any time.
