#!/usr/bin/env python3
# Spec: knowledge/operations/context-safety.md
"""Fail-closed hook adapter. Never echo event or transcript content."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/context"))
from budget import handle, stop

event = {}
try:
    event = json.loads(sys.stdin.read(2 * 1024 * 1024))
    print(json.dumps(handle(ROOT, event)))
except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError):
    name = event.get("hook_event_name") if isinstance(event, dict) else None
    print(json.dumps(stop(name, "Æion Factory context verification unavailable; refusing further work.")))
    sys.exit(0)
