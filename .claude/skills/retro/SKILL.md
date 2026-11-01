---
name: retro
description: The weekly retrospective - reads the recent sessions and the owner's pull request comments, and turns repeated errors, repeated corrections, stated preferences and redone procedures into hook rules, skill steps, new skills and preferences, in one pull request. Use weekly or after a long session.
---

# Retro (hindsight)

## Process
1. Gather: this project's Claude Code transcripts of the last week (`~/.claude/projects/<project>/*.jsonl`, when present locally), merged PRs and their review comments, outer-loop issues.
2. Extract, with one line of evidence each: an error repeated; a correction made twice; a stated preference; a procedure redone by hand.
3. Turn each into the cheapest durable fix:
   - a regex can see it → a `hookify` rule (`.claude/hookify.<name>.local.md`, warn first);
   - it needs judgement → a step or red flag in the right skill;
   - a new repeated procedure → a new skill, drafted and evaluated with `skill-creator`;
   - a preference → `knowledge/policies/owner-preferences.md` (skill `pr-taste` rules).
4. Measure the trinity (tokens per merged PR, time to merge, share merged without human edits) and add one line to `work/current.md`.
5. One PR on `task/retro-<date>`; skill `pr-review`.

## Red flags
Copying transcript text; storing personal data or a secret; ten new rules a week (keep the few that matter).

## Verification
- [ ] Each change cites its evidence line.

## Prove that a rule is worth keeping
Use only authorized project-local evidence; never scan all users' histories or provider state.
Prefer a narrow correction to the owning skill over another skill or hook. Check whether the
error came from missing instructions, missing tools, unavailable permission or a wrong runtime
assumption before adding prose. Record the evidence and a realistic counterexample so the rule
does not block legitimate work. Do not claim token/time improvements without comparable runs.
