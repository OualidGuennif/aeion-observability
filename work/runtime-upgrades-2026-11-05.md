# Factory 2.0.3 and Langfuse 4.75.0 — verified local upgrade

The owner authorized both upgrades and complete factory delivery. These upgrade results do not
certify PostgreSQL/React product delivery or an end-to-end feature merge.

## Factory

Adopted the exact official v2.0.3 tag, `162ca035292941f75752d2b1a4ffb2db955194d6`.
The project marker is `.aeion-factory`; application `VERSION` remains independent. Project
rules, CI jobs, empty passive skill catalog, credits and hook regression cases were preserved.
The owner completed the owner-only mode migration; actual local Git configuration reads `team`.

Verification: 28/28 connectors, 57 hooks and the complete upstream Factory suite pass. Evidence:
`/private/tmp/aeion-factory203-tests-02gu3sdh`. No sibling source checkout was modified.

Independent GLM/Qwen reviews retained their original verdicts and costs. Qwen's contextual
follow-up identified Git transport program overrides in the writing-job allowlist. Nine
regression cases passed the guard before correction; all are now refused, including helper
URLs after `--`, abbreviated transport options and nested shells. The complete hook suite
passes728 checks; all17 loop tests pass. This hardens the shared guard, without claiming the
allowlist is a universal shell sandbox. A fresh exact-head review is required before push.

## Langfuse

Official latest stable release checked on November 4: [4.75.0](https://github.com/langfuse/langfuse/releases/tag/v4.75.0).
Both deployed services are pinned by immutable digest in `demo/compose.yaml`. Before migration,
all five private data volumes were cold-snapshotted, archive-checked and SHA256-hashed. Private
backup receipt: `demo/.local/backups/langfuse-pre-4.75.0-vw3sreel/receipt.json`. No original volume
was deleted, reset or overwritten. Backup data stays ignored and owner-only.

Actual health returns version4.75.0. Web/worker run without restarts. Prisma unfinished0,
background failed0, finished9. One pending job is optional destructive cleanup of old sorting
tables, disabled by default; it was deliberately not enabled. See the official
[v4 upgrade procedure](https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4).

Historical real GLM/Qwen review traces remain readable. A fresh native OTLP canary is stored in
`demo/.local/upgrades/langfuse-4.75.0/latest-readback.json`, trace2dbdbcf730b0470f5fce56805f1f6382.
The first canary exposed a collector filter omission: bounded reasoning_effort was dropped.
Both trace/log filters now preserve only that enum in addition to their existing allowlist.
The repeated canary confirms preservation and removal of private content. No provider inference
was invoked by the canary. Previous failure evidence is retained, not relabelled as success.

## Remaining delivery

Qualify native factory tools independently of product delivery, then dispatch actual product
MDs through Flue/Pi/OpenShell. Each candidate must pass external product acceptance and two
independent reviewer families before PR/exact-head CI/confirmed main. PostgreSQL migration,
SQLite integrity/restore and React production/browser flows still need actual product evidence.
