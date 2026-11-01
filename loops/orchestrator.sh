#!/usr/bin/env bash
# Runs one loop job headless with Claude Code: its prompt, model, thinking level, tool allowlist
# and an optional spend cap. Prints the settings; runs nothing while LOOPS_ENABLED is not true.
# Spec: knowledge/operations/loops.md
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
usage() { echo "usage: loops/orchestrator.sh <inner|middle|outer|docs|security|watch|retro> [--dry-run] [--issue N]" >&2; exit 64; }

JOB="${1:-}"; [[ -n "$JOB" ]] || usage; shift
DRY_RUN=false; ISSUE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --issue) ISSUE="${2:-}"; shift ;;
        *) usage ;;
    esac
    shift
done

# Read only the loop settings from env.local: never sourced as shell, never the Decisions API
# secret, so nothing sensitive reaches the agent's environment.
setting() {
    local key="$1" default="$2" value=""
    if [[ -f "$ROOT/env.local" ]]; then
        value="$(grep -E "^${key}=" "$ROOT/env.local" | tail -1 | cut -d= -f2- | sed 's/[[:space:]]*#.*$//; s/[[:space:]]*$//')"
    fi
    printf '%s' "${value:-$default}"
}

# Each job: prompt file, criticality (low|normal|high), tool allowlist, permission mode.
READ_ONLY="Read,Grep,Glob,Write(.aeion/loop-bodies/**),Bash(git log -5 --oneline),Bash(git diff --stat),Bash(git diff --check),Bash(git status --short),Bash(tools/knowledge/knowledge-check),Bash(tools/knowledge/doc-links),Bash(tools/knowledge/doc-links --for *),Bash(tools/repo-health/repo-health),Bash(gh issue list *),Bash(gh issue view *),Bash(gh issue create *),Bash(gh issue comment *)"
case "$JOB" in
    inner)    PROMPT="inner.md";    CRIT="normal"; MODE="acceptEdits"
              TOOLS="Read,Grep,Glob,Edit,Write,Agent,Bash(git *),Bash(gh issue *),Bash(gh pr *),Bash(tools/*),Bash(python3 *)"
              [[ "$ISSUE" =~ ^[0-9]+$ ]] || { echo "inner needs a numeric --issue N" >&2; exit 64; } ;;
    middle)   PROMPT="middle.md";   CRIT="normal"; MODE="dontAsk"; TOOLS="$READ_ONLY,Agent,Bash(gh pr list *),Bash(gh pr view *),Bash(gh pr checks *),Bash(gh pr diff *),Bash(gh pr comment *)" ;;
    outer)    PROMPT="outer.md";    CRIT="low";    MODE="dontAsk"; TOOLS="$READ_ONLY,Bash(gh issue *),Bash(gh run list *)" ;;
    docs)     PROMPT="docs.md";     CRIT="low";    MODE="dontAsk"; TOOLS="$READ_ONLY,Bash(gh issue *)" ;;
    security) PROMPT="security.md"; CRIT="high";   MODE="dontAsk"; TOOLS="$READ_ONLY,Agent,Skill,Bash(gh issue *)" ;;
    watch)    PROMPT="watch.md";    CRIT="normal"; MODE="acceptEdits"
              TOOLS="$READ_ONLY,WebSearch,WebFetch,Write(tech-watch/**),Edit(tech-watch/**),Bash(git *),Bash(gh pr create *)" ;;
    retro)    PROMPT="retro.md";    CRIT="normal"; MODE="acceptEdits"
              TOOLS="$READ_ONLY,Agent,Write(knowledge/**),Edit(knowledge/**),Write(.claude/**),Edit(.claude/**),Bash(git *),Bash(gh pr *),Bash(gh api *)" ;;
    *) usage ;;
esac
ENABLED="$(setting LOOPS_ENABLED false)"
if [[ "$JOB" == inner && "$DRY_RUN" == false && "$ENABLED" == true ]]; then
    LABELS="$(cd "$ROOT" && gh issue view "$ISSUE" --json labels --jq '.labels[].name')"
    grep -Fxq "agent-ready" <<< "$LABELS" || { echo "issue is not agent-ready; nothing runs" >&2; exit 3; }
    if grep -Fxq "severity:high" <<< "$LABELS"; then CRIT=high; fi
fi
# A production read is allowed only through the configured read-only command.
PROD_READ="$(setting PROD_READ_COMMAND "")"
[[ "$JOB" == outer && -n "$PROD_READ" ]] && TOOLS="$TOOLS,Bash(${PROD_READ}*)"

# Model and thinking level: a pinned value wins; `auto` follows the job's criticality.
PREFIX="$(printf '%s' "$JOB" | tr '[:lower:]' '[:upper:]')"
case "$JOB" in inner|middle|outer) KEY="${PREFIX}_LOOP" ;; retro) KEY="RETRO" ;; *) KEY="OUTER_LOOP" ;; esac
MODEL="$(setting "${KEY}_MODEL" auto)"; EFFORT="$(setting "${KEY}_THINKING_LEVEL" auto)"
if [[ "$MODEL" == auto ]]; then
    case "$CRIT" in low) MODEL=haiku ;; high) MODEL=opus ;; *) MODEL=sonnet ;; esac
fi
if [[ "$EFFORT" == auto ]]; then
    case "$CRIT" in low) EFFORT=low ;; high) EFFORT=high ;; *) EFFORT=medium ;; esac
fi

PROMPT_TEXT="$(cat "$HERE/prompts/$PROMPT")"
[[ -n "$ISSUE" ]] && PROMPT_TEXT="$PROMPT_TEXT

The issue to fix: #$ISSUE."
CMD=("$ROOT/tools/context/run" -p "$PROMPT_TEXT" --model "$MODEL" --effort "$EFFORT" --permission-mode "$MODE"
     --allowedTools "$TOOLS" --output-format text)
MAX_TURNS="$(setting LOOP_MAX_TURNS 30)"
DEADLINE="$(setting LOOP_TIMEOUT_SECONDS 900)"
[[ "$MAX_TURNS" =~ ^[1-9][0-9]*$ && "$DEADLINE" =~ ^[1-9][0-9]*$ ]] || { echo "loop turn/time limits must be positive integers" >&2; exit 64; }
CMD+=(--max-turns "$MAX_TURNS")
# A spend cap applies to API billing; on a subscription it is ignored.
BUDGET="$(setting LOOP_MAX_BUDGET_USD "")"
[[ -n "$BUDGET" ]] && CMD+=(--max-budget-usd "$BUDGET")

echo "job=$JOB model=$MODEL effort=$EFFORT mode=$MODE budget=${BUDGET:-none} max_turns=$MAX_TURNS timeout=$DEADLINE" >&2
echo "tools=$TOOLS" >&2
if [[ "$DRY_RUN" == true ]]; then
    echo "dry run: nothing executed" >&2
    exit 0
fi
if [[ "$ENABLED" != true ]]; then
    echo "LOOPS_ENABLED is not true in env.local: nothing runs" >&2
    exit 0
fi

# Run from the repository root; keep the log out of git.
mkdir -p "$ROOT/.aeion/logs"
LOG="$ROOT/.aeion/logs/${JOB}-$(date -u +%Y%m%dT%H%M%SZ).log"
cd "$ROOT"
case "$JOB" in outer|docs|security|middle) export AEION_LOOP_READ_ONLY=1 ;; esac
[[ "$JOB" == outer && -n "$PROD_READ" ]] && export AEION_PROD_READ_COMMAND="$PROD_READ"
python3 "$ROOT/tools/loops/run" --timeout "$DEADLINE" -- "${CMD[@]}" > "$LOG" 2>&1 || { echo "loop $JOB failed; see $LOG" >&2; exit 1; }
echo "loop $JOB done; log $LOG" >&2
