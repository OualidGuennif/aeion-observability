"""Print which readiness condition blocks a live tier-3 run, without echoing any secret."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import os

import settings  # noqa: F401  (loads the private stack file into the environment)
from sandbox import cli_qualified, protocol_hash

report = {
    "opencode_key_present": bool(os.environ.get("OPENCODE_API_KEY")),
    "openshell_endpoint_present": bool(os.environ.get("OPENSHELL_ENDPOINT")),
    "agent_image_present": bool(os.environ.get("OPENSHELL_AGENT_IMAGE")),
    "agent_uid": settings.AGENT_UID,
}
try:
    report["protocol_hash"] = protocol_hash()[:16]
except KeyError as exc:
    report["protocol_hash_error"] = str(exc)
report["cli_qualified"] = cli_qualified()
marker = settings.DATA / "cli-qualification.json"
report["marker_exists"] = marker.is_file()
if marker.is_file():
    import json
    recorded = json.loads(marker.read_text())
    report["marker_protocol"] = recorded["protocol_sha256"][:16]
report["context_blocked"] = (settings.DATA / "context.blocked").exists()
try:
    from server import sandbox_ready
    report["sandbox_ready"] = sandbox_ready()
except Exception as exc:  # noqa: BLE001 - report, never raise from a diagnostic
    report["sandbox_ready_error"] = f"{type(exc).__name__}:{exc}"
import json as _json
print(_json.dumps(report, indent=2, sort_keys=True))
