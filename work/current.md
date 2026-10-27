# Current work

## OpenShell isolation and task-specific model lab
- Owner decision: Require OpenShell for every build/check execution, disable NVIDIA telemetry, broaden paid Go task/model comparisons, preserve MD-before-reset and 250k/300k gates, retain analyses/decisions in Hindsight, then publish through PR and merge main. Explicitly approved in chat, most recently 2026-10-27.
- State: Implemented on task/openshell-safe-model-lab. Local OpenShell security probes, real CLI/fake-inference handover, all five official tokenizer templates and four protected scenario contracts pass. Paid campaign, final backend/UI verification and hosted CI are being completed.
- Next: Run the comparable Go campaign, verify backend receipts and browser behavior, finish evidence, then PR/merge/main publication.
- Blocker: No implementation approval is missing. General model superiority, invoices and hostile-code/production qualification remain outside this small lab's evidence.
- Evidence: demo/README.md; knowledge/components/docker-demo.md; demo/openshell/; demo/tests/; work/validation.md.
