"""Bounded file queue between the worker and the publisher.

The worker cannot hold the publish credential, so it does not publish: it writes a request
here and stops. A separate publisher process drains the queue with the publish credential
loaded for that one run. Files are JSON, size-capped, written atomically and named by attempt.
"""
import json
import os
from pathlib import Path

MAX_REQUEST_BYTES = 1024 * 1024


class QueueError(ValueError):
    """A publish request that cannot be queued or read."""


def _folder(state_dir):
    path = Path(state_dir) / "publish-queue"
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def enqueue(state_dir, request):
    """Write one request atomically; the attempt id is the idempotency key."""
    body = json.dumps(request, sort_keys=True).encode("utf-8")
    if len(body) > MAX_REQUEST_BYTES:
        raise QueueError("request_too_large")
    attempt = request.get("attempt_id")
    if not attempt or not isinstance(attempt, str):
        raise QueueError("missing_attempt_id")
    target = _folder(state_dir) / f"{attempt}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(body)
    os.chmod(temporary, 0o600)
    temporary.replace(target)
    return str(target)


def pending(state_dir):
    """List queued requests in creation order, without reading their bodies."""
    folder = _folder(state_dir)
    return sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime_ns)


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise QueueError("unreadable_request") from exc


def done(state_dir, request_or_path, outcome):
    """Move a drained request to the results folder with its outcome."""
    folder = _folder(state_dir) / "done"
    folder.mkdir(parents=True, exist_ok=True)
    source = Path(request_or_path)
    body = {"request": read(source), "outcome": outcome}
    target = folder / source.name
    target.write_text(json.dumps(body, sort_keys=True))
    os.chmod(target, 0o600)
    source.unlink(missing_ok=True)
    return str(target)
