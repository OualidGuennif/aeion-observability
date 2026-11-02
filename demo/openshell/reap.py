"""Reap orphaned OpenShell Docker containers left behind by an interrupted run.

The gateway normally deletes both containers of a sandbox. A killed qualification or a gateway
restart can leave the supervisor/sandbox pair running with nothing tracking them, which burns CPU
forever. This host-side tool removes only containers carrying OpenShell's own managed-by label
and only when two independent facts hold: the container is older than the safety window, and no
factory build lease is active. It never touches the Langfuse, cockpit or forum containers.

Age alone cannot tell a long build from an orphan: a live build holds a dispatch lease in the
factory store for as long as its sandbox may run. The store is read read-only; an unreadable store
is not evidence that nothing is running, so the sweep is refused rather than guessed.

Dry run by default:

    python3 demo/openshell/reap.py --older-than 3600
    python3 demo/openshell/reap.py --older-than 3600 --execute
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

LABEL = "openshell.ai/managed-by=openshell"
NAMESPACE = "aeion-observability"
DEFAULT_OLDER_THAN = 3600
DEFAULT_STORE = Path(__file__).resolve().parents[2] / "demo" / ".local" / "factory" / "factory.db"
UNSAFE_LEASES = {"active", "unknown"}


def _docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


def created_timestamp(value):
    """Docker's RFC3339Nano timestamp to epoch seconds; malformed evidence is skipped."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def container_ages(ids, now=None, docker=None):
    """Return [(id, name, age_seconds)] for containers whose creation time is readable."""
    now = time.time() if now is None else now
    docker = docker or _docker
    result = []
    for container_id in ids:
        try:
            payload = json.loads(docker("inspect", container_id).stdout)[0]
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError, TypeError):
            continue
        created = created_timestamp(payload.get("Created"))
        if created is None:
            continue
        name = str(payload.get("Name") or container_id).lstrip("/")
        result.append((container_id, name, max(0.0, now - created)))
    return result


def stale_ids(ids, older_than=DEFAULT_OLDER_THAN, now=None, docker=None):
    return [container_id for container_id, _, age in container_ages(ids, now=now, docker=docker)
            if age >= older_than]


def managed_ids(docker=None):
    docker = docker or _docker
    result = docker("ps", "-q", "--filter", f"label={LABEL}",
                    "--filter", f"label=openshell.ai/sandbox-namespace={NAMESPACE}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def lease_state(store=None, now=None):
    """Whether a dispatched build could still own a sandbox.

    ``absent`` means the factory never created its store, so no build can hold a lease;
    ``unknown`` means the store exists but cannot be read, and the caller must not reap.
    """
    path = Path(store) if store is not None else DEFAULT_STORE
    try:
        path.stat()
    except FileNotFoundError:
        # The factory never created its store, so no build can hold a lease.
        return {"state": "absent", "count": 0}
    except OSError:
        # Present but not stat-able is not evidence that nothing runs.
        return {"state": "unknown", "count": None}
    horizon = int((time.time() if now is None else now) * 1_000_000_000)
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=5)
        try:
            row = connection.execute(
                "SELECT COUNT(*), MAX(lease_until_ns) FROM builds "
                "WHERE status='dispatched' AND lease_until_ns > ?", (horizon,)).fetchone()
        finally:
            connection.close()
    except (sqlite3.Error, ValueError):
        return {"state": "unknown", "count": None}
    count = int(row[0] or 0)
    if count:
        return {"state": "active", "count": count, "until_ns": row[1]}
    return {"state": "idle", "count": 0}


def sweep(older_than=DEFAULT_OLDER_THAN, execute=False, now=None, docker=None, store=None):
    """List the stale containers, gate removal on the leases, and remove only when allowed.

    Containers are listed before the lease is read: a lease claimed between the two is then seen,
    and a sandbox started after it cannot be in the list. Removal happens after the same read.
    """
    docker = docker or _docker
    aged = [(container_id, name)
            for container_id, name, age in container_ages(managed_ids(docker), now=now, docker=docker)
            if age >= older_than]
    leases = lease_state(store=store, now=now)
    blocked = f"build_lease_{leases['state']}" if leases["state"] in UNSAFE_LEASES else None
    removed = []
    if execute and not blocked:
        for container_id, name in aged:
            docker("rm", "-f", container_id)
            removed.append(name)
    return {
        "execute": bool(execute),
        "leases": leases,
        "blocked": blocked,
        "count": len(aged),
        "containers": [name for _, name in aged],
        "removed": removed,
    }


def reap(older_than=DEFAULT_OLDER_THAN, execute=False, now=None, docker=None, store=None):
    """Return the containers this sweep removed, or the ones it would remove in a dry run."""
    report = sweep(older_than=older_than, execute=execute, now=now, docker=docker, store=store)
    return report["removed"] if execute else report["containers"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--older-than", type=int, default=DEFAULT_OLDER_THAN,
                        help="seconds a container must have existed before it is stale")
    parser.add_argument("--execute", action="store_true", help="actually remove; default is a dry run")
    parser.add_argument("--store", default=str(DEFAULT_STORE),
                        help="factory SQLite state read to confirm no build lease is active")
    args = parser.parse_args(argv)
    if args.older_than < 600:
        parser.error("--older-than must be at least 600 seconds")
    report = sweep(older_than=args.older_than, execute=args.execute, store=args.store)
    print(json.dumps(report, indent=2))
    # A requested removal that the lease gate held is a failed command, not a quiet success.
    return 1 if (args.execute and report["blocked"]) else 0


if __name__ == "__main__":
    sys.exit(main())
