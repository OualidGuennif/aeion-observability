#!/usr/bin/env python3
# Spec: knowledge/policies/security.md
"""Refuse secret paths and unbounded large reads before native tool execution (exit 2)."""
import json
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath
from secret_names import brace_variants, is_secret, named_secrets

MAX_INTAKE_BYTES, MAX_INTAKE_LINES = 65536, 400
MAX_SCAN_BYTES = 1024 * 1024
INTAKE_REASON = ("bounded intake: use a Read window of at most 400 lines, head -c 65536, "
                 "or a targeted search with a positive result limit (knowledge/policies/bounded-intake.md)")

def deny(reason):
    print(f"Blocked by .claude/hooks/guard-path.py: {reason} (knowledge/policies/security.md).", file=sys.stderr)
    sys.exit(2)


def check_intake(path, tool, data):
    # An explicit unlimited content search is unbounded wherever it runs, including directories.
    limit = data.get("head_limit", data.get("limit"))
    if tool == "Grep" and type(limit) is int and limit == 0 and data.get("output_mode") not in {"count", "files_with_matches"}:
        deny(INTAKE_REASON)
    if tool not in {"Read", "Grep"} or not path:
        return
    target = Path(path)
    try:
        if not target.exists() or target.is_dir():
            return
        if not target.is_file():
            deny(INTAKE_REASON)
        if tool == "Grep":
            limit = data.get("head_limit", data.get("limit"))
            if data.get("output_mode") in {"count", "files_with_matches"} or (type(limit) is int and 0 < limit <= MAX_INTAKE_LINES):
                return
            limit, offset = None, 1
        else:
            # Read accepts offset 0 as the start of the file, the same window as offset 1.
            limit, offset = data.get("limit"), data.get("offset", 1)
            offset = 1 if type(offset) is int and offset == 0 else offset
        bounded = type(limit) is int and 0 < limit <= MAX_INTAKE_LINES
        if type(offset) is not int or offset < 1:
            deny(INTAKE_REASON)
        if not bounded and target.stat().st_size > MAX_INTAKE_BYTES:
            deny(INTAKE_REASON)
        scanned, total, count = 0, 0, 0
        with target.open("rb") as stream:
            for index in range(offset - 1 + (limit if bounded else MAX_INTAKE_LINES + 1)):
                line = stream.readline(MAX_SCAN_BYTES - scanned + 1)
                if not line:
                    break
                scanned += len(line)
                if scanned > MAX_SCAN_BYTES:
                    deny(INTAKE_REASON)
                if index >= offset - 1:
                    total, count = total + len(line), count + 1
                    if total > MAX_INTAKE_BYTES or count > MAX_INTAKE_LINES:
                        deny(INTAKE_REASON)
    except OSError:
        deny("the intake size could not be verified; " + INTAKE_REASON)


try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    deny("the hook input could not be read; refusing rather than guessing")
if not isinstance(event, dict) or not isinstance(event.get("tool_input"), dict):
    deny("the hook event must contain a tool_input object")
tool_input = event["tool_input"]
path = tool_input.get("file_path", tool_input.get("filePath", tool_input.get("path", tool_input.get("notebook_path"))))
if path is None and event.get("tool_name") == "Grep":
    path = ""
elif not isinstance(path, str) or (not path and event.get("tool_name") != "Grep"):
    deny("the tool path must be a nonempty string")
if "\0" in path:
    deny("the tool path contains a null byte")
name = PurePosixPath(path).name
if is_secret(name):
    print(f"Blocked by .claude/hooks/guard-path.py: {name} holds secrets and is never opened "
          f"(knowledge/policies/security.md).", file=sys.stderr)
    sys.exit(2)
# Writing the git config file sets aeion.mode or core.hooksPath without guard-bash's git config checks.
# The path is normalized and case folded: .git//config and .GIT/Config are the same file on APFS.
if event.get("tool_name") not in {"Read", "Grep", "Glob"} and re.search(
        r"(^|/)\.git/(config|config\.worktree|worktrees/[^/]+/config\.worktree)$", posixpath.normpath(path).lower()):
    deny("the git config file is changed with git config, never edited directly")
# Grep's glob filter picks the files it reads, so a glob that names a secret is a read of it.
if event.get("tool_name") == "Grep" and tool_input.get("glob") is not None:
    if not isinstance(tool_input["glob"], str):
        deny("the Grep glob must be a string")
    try:
        names = [PurePosixPath(p).name for p in brace_variants(tool_input["glob"])]
    except ValueError:
        deny("the Grep glob could not be verified; name the files explicitly")
    if any(is_secret(n) or named_secrets(n) for n in names):
        deny("the Grep glob names a secret file, which is never opened")
check_intake(path, event.get("tool_name", "Read"), tool_input)
sys.exit(0)
