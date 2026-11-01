#!/usr/bin/env python3
# Spec: knowledge/operations/agent-compatibility.md
"""The files every harness reads from a project, and the configs a project may edit itself.

One list with two callers: the drift check compares a project's copies against a reference, and the
template update writes those copies from it. A second copy of this list would drift from the first,
which is the failure both tools exist to catch.

    from connectors import CONTRACT, MERGE, WIRING
"""

# The shared readers travel with the connectors: a project's check imports them.
CONTRACT = (
    "tools/agents/hook.py",
    "tools/agents/run",
    "tools/context/budget.py",
    "tools/context/run",
    ".claude/hooks/after-edit.py",
    ".claude/hooks/context-budget.py",
    ".claude/hooks/guard-bash.py",
    ".claude/hooks/guard-path.py",
    ".claude/hooks/project_files.py",
    ".claude/hooks/prompt-defense.py",
    ".claude/hooks/secret_names.py",
    ".claude/hooks/session-start.py",
    ".claude/hooks/sign-off.py",
    ".claude/hooks/token-feedback.py",
    ".dsh/factory.patch.yml",
    "tools/agents/connectors.py",
    "tools/agents/refs.py",
    ".dsh/plugins/factory/index.js",
    ".dsh/plugins/factory/seam.js",
    ".dsh/plugins/factory/compaction.js",
    ".pi/extensions/factory/index.js",
    ".opencode/plugins/factory/index.js",
    ".opencode/plugins/factory/package.json",
    ".codex/hooks.json",
    ".devin/hooks.v1.json",
    ".factory/settings.json",
    ".agents/hooks.json",
)

WIRING = (
    ".claude/settings.json",
    ".codex/hooks.json",
    ".codex/config.toml",
    ".devin/hooks.v1.json",
    ".devin/config.json",
    ".factory/settings.json",
    ".agents/hooks.json",
    ".dsh/factory.patch.yml",
)

# A project owns these: its instructions and its merged settings win over the factory's.
MERGE = (
    "AGENTS.md",
    ".claude/settings.json",
    ".codex/config.toml",
    ".devin/config.json",
)
