"""Host-native locations and loopback service endpoints; the environment overrides each one."""
import os
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
LOCAL = Path(os.environ.get("AEION_LOCAL_DIR", DEMO / ".local"))


def _load_stack_env(path):
    """Load a private KEY=VALUE file into the environment; real values always win.

    Values are never logged or echoed, and a missing file is simply skipped.
    """
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


# The owner keeps the credentials in one private file at the repository root; the demo's own
# stack file comes second and only fills what is still unset.
_load_stack_env(DEMO.parent / ".env")
_load_stack_env(LOCAL / "stack.env")

# Separation of powers: this process writes code, so it must never hold a credential that can
# publish, release or merge. One list, owned by factory/keys.py so the roles cannot drift apart.
import sys  # noqa: E402

if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))
from factory.keys import PUBLISH_CREDENTIALS  # noqa: E402


def _scrub_publish_credentials():
    removed = [name for name in PUBLISH_CREDENTIALS if os.environ.pop(name, None) is not None]
    return removed


SCRUBBED_CREDENTIALS = _scrub_publish_credentials()

DATA = Path(os.environ.get("AEION_DATA_DIR", LOCAL / "data"))
WORK = Path(os.environ.get("AEION_WORK_DIR", LOCAL / "work"))
HARNESS = LOCAL / "harness"
FLUE = DEMO / "flue"
OPENSHELL_STATE = LOCAL / "openshell"
FACTORY_STATE = LOCAL / "factory"
FACTORY_MANIFEST = DEMO / "forum/features/MANIFEST.json"
FACTORY_SPEC_DIR = DEMO / "forum/features"
# Operator-labeled Docker volume backed by WORK; OpenShell admits it by label, never a raw host path.
WORK_VOLUME = "aeion-openshell-work"

OTEL_TRACES = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
OTEL_LOGS = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "http://127.0.0.1:4318/v1/logs")
LANGFUSE_URL = os.environ.get("LANGFUSE_URL", "http://127.0.0.1:3300")
SERVICES = {
    "otel": ("http://127.0.0.1:13133", "/"),
    "langfuse": (LANGFUSE_URL, "/api/public/health"),
    "hindsight": (os.environ.get("HINDSIGHT_URL", "http://127.0.0.1:8889"), "/health"),
    "claude_mem": (os.environ.get("CLAUDE_MEM_URL", "http://127.0.0.1:37777"), "/health"),
    "playground": (os.environ.get("PLAYGROUND_URL", "http://127.0.0.1:8090"), "/health"),
}
# Linux sandboxes run as the host user so bind-mounted files stay owned by it; Docker
# Desktop maps ownership itself, so macOS keeps the image's dedicated agent UID.
AGENT_UID = int(os.environ.get("AEION_AGENT_UID", "10001"))
