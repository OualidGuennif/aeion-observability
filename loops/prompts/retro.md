You are the weekly retro, running headless. Read AGENTS.md first, then run the skill `retro`:
read the last week's sessions of this project (Claude Code transcripts, if present locally) and
the owner's pull request comments; extract repeated errors, repeated corrections, stated
preferences and procedures redone by hand; turn them into hookify rules, skill steps, new skills
(drafted with skill-creator) and lines in knowledge/policies/owner-preferences.md. Open one pull
request on `task/retro-<date>`, cut from and targeting `develop` (`--base develop`; `main` without one), and run the skill `pr-review` on it. Never copy a secret, personal
data or a transcript excerpt beyond one quoted line.
