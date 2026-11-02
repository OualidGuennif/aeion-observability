"""Print which readiness condition blocks a live tier-3 run, without echoing any secret.

The diagnostic reports; it must never become the cockpit. It therefore talks to the sandbox
helper directly instead of importing ``demo/app/server.py``, whose module body starts the
factory thread and serves HTTP.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import settings  # noqa: F401  (loads the private stack file into the environment)
from sandbox import cli_qualified, protocol_hash


def sandbox_ready(timeout=2):
    """Ask the sandbox helper for a connection; a missing sandbox is a report, not a crash."""
    from sandbox import connection

    try:
        client = connection(timeout=timeout)
        client.close()
        return True
    except Exception:  # noqa: BLE001 - a diagnostic reports, never raises
        return False


def build_report():
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
        recorded = json.loads(marker.read_text())
        report["marker_protocol"] = recorded["protocol_sha256"][:16]
    report["context_blocked"] = (settings.DATA / "context.blocked").exists()
    try:
        report["sandbox_ready"] = sandbox_ready()
    except Exception as exc:  # noqa: BLE001 - report, never raise from a diagnostic
        report["sandbox_ready_error"] = f"{type(exc).__name__}:{exc}"
    return report


def main():
    print(json.dumps(build_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
