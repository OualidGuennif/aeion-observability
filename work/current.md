# Current work

## Local agent observability and memory showcase
- Owner decision: Add a Docker Langfuse/OTel demo, Deno JS/Hono target, Python cockpit, Go-backed OpenCode build agents, Hindsight and claude-mem; require Markdown before reset, 250k handover and independent 300k admission guard. Implementation and subsequent PR/main publication approved in chat, 2026-10-25.
- State: Implemented on task/langfuse-opencode-demo; both paid Go profiles passed the protected 12-check task. Local checks, real Go tasks, backend reads, handover qualification and browser QA passed; publication through the PR workflow is authorized.
- Next: Use demo/README.md for presentation and restart commands; hosted CI and publication state are available in the release PR.
- Blocker: None for the local pilot. General model ranking, invoices and production runtime qualification remain outside the measured evidence.
- Evidence: demo/README.md; knowledge/components/docker-demo.md; demo/tests/; demo/verify_backend.py; work/validation.md.
