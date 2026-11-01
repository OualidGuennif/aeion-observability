# Model routing

`env.local` sets each loop's model and thinking level; `auto` (the default) follows the job's
criticality in `orchestrator.sh`:

| Criticality | Jobs | Model | Thinking |
| --- | --- | --- | --- |
| low | outer health, docs drift | a small, fast model (`haiku`) | low |
| normal | inner fixes, middle reviews, watch, retro | a balanced model (`sonnet`) | medium |
| high | security scans; any issue labelled `severity:high` | the most capable model (`opus`) | high |

A pinned value (`INNER_LOOP_MODEL=opus`, `OUTER_LOOP_THINKING_LEVEL=medium`) overrides `auto`.
Aliases resolve to the newest model of each family in Claude Code. Raise a level only when a
measurement (the trinity of Phase 7) shows the lower one failing; lower it when it does not.
