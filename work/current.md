# Current work

## OpenShell isolation and task-specific model lab
- Owner decision: Require OpenShell for every build/check execution, disable NVIDIA telemetry, broaden paid Go task/model comparisons, preserve MD-before-reset and 250k/300k gates, retain analyses/decisions in Hindsight, then publish through PR and merge main. Explicitly approved in chat, most recently 2026-10-27.
- State: Implementation verified. The corrected five-model/four-task campaign completed 40 attempts: 36 accepted outcomes, four retained CLI failures, complete native usage and $0.368068181 in CLI estimates. Four-tool readbacks, a measured Auto build, the synthetic 250k replay and browser checks pass. Published to `main` through [PR #4](https://github.com/OualidGuennif/aeion-observability/pull/4).
- Next: Refresh dated sandbox/CLI qualifications before later live runs when expired. Requalify DeepSeek privacy after 2026-10-31 before using that profile again. Collect representative task evidence before applying these observations beyond the demo.
- Blocker: None for the qualified local demo. General model superiority, invoices and hostile-code/production qualification remain outside this small lab's evidence.
- Evidence: [validation and receipts](validation.md); [demo runbook](../demo/README.md); [component](../knowledge/components/docker-demo.md); demo/openshell/; demo/tests/.

## Repository review follow-ups
- Owner decision: Fix reviewed defects that leave the qualified protocol hash unchanged first; handle protocol-hashed fixes as a separate requalified change. Approved in chat, 2026-10-27.
- State: First batch merged in [PR #5](https://github.com/OualidGuennif/aeion-observability/pull/5). Second batch implemented on a separate branch: unloadable artifacts fail every check, the hook publishes its state files atomically, one cost-stop default, dead harness code removed, per-task check totals in the cockpit and host-level demo checks in CI.
- Next: Merge the second batch after hosted CI, then rerun `demo/openshell/setup.py`, rebuild the stack and rerun `qualify_cli.py` locally: the protocol hash and agent image change.
- Blocker: Local live runs stay blocked until that requalification; hosted CI exercises the same OpenShell qualification on Linux.
- Evidence: [first batch](validation.md#repository-review-follow-ups--2026-10-27); [second batch](validation.md#protocol-review-follow-ups--2026-10-27).
