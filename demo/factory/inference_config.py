"""Load the existing named inference role without a second model-call engine.

Spec: knowledge/components/factory-flue.md
"""
import os
from pathlib import Path

ENVIRONMENT_KEYS = ('OPENCODE_API_KEY',)


def available():
    load_environment()
    return bool(os.environ.get("OPENCODE_API_KEY"))


def load_environment(paths=None):
    """Load only the provider keys from the project's existing dotenv files.

    Values are never logged or returned. An already-exported variable wins, so an operator
    can override a stored file without editing it. Returns the names that were loaded.
    """
    root = Path(__file__).resolve().parents[2]
    candidates = paths or [root / "demo/.local/stack.env", root / "demo/.env", root / ".env"]
    loaded = []
    for path in candidates:
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            if key not in ENVIRONMENT_KEYS or key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ[key] = value
                loaded.append(key)
    return loaded
