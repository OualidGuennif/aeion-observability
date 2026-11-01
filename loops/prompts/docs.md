You are the docs job of the outer loop, running headless and read-only. Read AGENTS.md first.

Run `tools/knowledge/knowledge-check`, `tools/knowledge/doc-links` and look for knowledge docs whose
`stale_after` date has passed or is within 14 days. For each finding not already tracked
(`gh issue list --label loop:outer`), run the skill `loop-triage` to open one issue with the exact
file and rule. If everything passes, say so in one line.
