# Codex integration

Read the [setup runbook](../knowledge/operations/agent-compatibility.md).
Codex reads root AGENTS.md and shared skills through ../.agents/skills.
Trust the project in Codex and review/enable its hooks in `/hooks`; project config and hook trust
are separate requirements. Untrusted projects intentionally ignore this folder.

The checked-in config enables native compaction at 250000 and local lifecycle hooks. Codex has no
compaction tool, so only its native threshold compacts: a compaction that comes before the verified
handover runs, and the session owes its closure right after it (a refusal would end every turn). The adapter
reuses Æion Factory's guards, edit feedback, sign-off reminder and verified pre-compaction handover.
It does not interpret Codex's unstable transcript format as a token API. No observed or strict
300k token stop is claimed for this adapter. Account/model/provider remain your existing choices.

Launch from a shell with `tools/agents/run codex`. CLI options are
native Codex options. Cloud-hosted orchestration can ignore local command hooks; qualify it
separately rather than assuming local behavior transfers.
