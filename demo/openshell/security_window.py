"""How long an OpenShell security proof may be reused. No probe and no docker here."""
import json
import time
from pathlib import Path

HOUR_NS = 3_600_000_000_000


def read_expiry(path):
    """Nanosecond expiry, or None when the file is missing or not a proof."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return None
    expires = data.get("expires_ns") if isinstance(data, dict) else None
    return expires if type(expires) is int else None


def needs_refresh(path, now_ns=None, margin_ns=HOUR_NS):
    """True when the proof is missing or inside the refresh margin."""
    expires = read_expiry(path)
    now = time.time_ns() if now_ns is None else now_ns
    return expires is None or expires - now < margin_ns


def still_unexpired(path, now_ns=None):
    """True when connection() would still accept this file on expiry alone."""
    expires = read_expiry(path)
    now = time.time_ns() if now_ns is None else now_ns
    return expires is not None and expires >= now


def publish_evidence(path, evidence):
    """Replace the proof only after the new bytes exist. The old file stays until then."""
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def ensure_fresh(path, probe, now_ns=None, margin_ns=HOUR_NS):
    """True when a sandbox may open.

    ``probe`` publishes a replacement or raises. It is not called while an hour or more
    remains. A failed probe still allows the open when the previous file has not expired.
    """
    now = time.time_ns() if now_ns is None else now_ns
    if not needs_refresh(path, now_ns=now, margin_ns=margin_ns):
        return True
    try:
        probe()
    except Exception:
        return still_unexpired(path, now_ns=now)
    after = time.time_ns() if now_ns is None else now_ns
    return (not needs_refresh(path, now_ns=after, margin_ns=margin_ns)
            or still_unexpired(path, now_ns=after))
